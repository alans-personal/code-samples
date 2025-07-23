package com.asnyder.gardener.api;

import static spark.Spark.*;

import com.amazonaws.services.dynamodbv2.model.AttributeValue;
import com.amazonaws.services.dynamodbv2.model.GetItemRequest;
import com.amazonaws.services.dynamodbv2.model.GetItemResult;
import com.google.gson.*;
import com.asnyder.gardener.api.dto.GardenParamStore;
import com.asnyder.gardener.api.dto.LambdaResultPayload;
import com.asnyder.gardener.api.dto.TagReader;
import com.asnyder.token.Verify;

import com.amazonaws.services.lambda.AWSLambda;
import com.amazonaws.services.lambda.AWSLambdaClientBuilder;
import com.amazonaws.services.lambda.model.InvokeRequest;
import com.amazonaws.services.lambda.model.InvokeResult;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;

import spark.Spark;

import io.jsonwebtoken.Claims;
import org.apache.commons.lang3.tuple.Pair;

import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.*;

public class Main {

    private final static Logger LOG = Logger.getLogger(Main.class.getName());

    private final static SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss Z");

    static{
        try {
            //ToDo... add file rotation to this, and modify the build to remove unneeded dependencies.
            FileHandler fh = new FileHandler("/home/ec2-user/gardener.%g.log", 5242880, 5, true);
            fh.setFormatter(new java.util.logging.Formatter() {
                @Override
                public String format(LogRecord logRecord) {
                    String timestamp = getTimestamp();
                    if(logRecord.getLevel() == Level.INFO) {
                        return "[INFO: "+timestamp+" ]  " + logRecord.getMessage() + "\r\n";
                    } else if(logRecord.getLevel() == Level.WARNING) {
                        return "[WARN: "+timestamp+" ]  " + logRecord.getMessage() + "\r\n";
                    } else if(logRecord.getLevel() == Level.SEVERE) {
                        return "[ERROR: "+timestamp+" ] ]  " + logRecord.getMessage() + "\r\n";
                    } else {
                        return "[OTHER: "+timestamp+" ]  " + logRecord.getMessage() + "\r\n";
                    }
                }
            });
            LOG.addHandler(fh);
        }catch (Exception ex){
            System.out.println();
        }
    }



    private static final Verify VERIFY = new Verify();

    private static final GardenParamStore gpStore = GardenParamStore.getInstance();
    private static final TagReader tagReader = TagReader.getInstance();
    private static final AtomicBoolean useJwt = new AtomicBoolean(false);

    public static void main(String[] args) {

        try {
            LOG.info("Gardener is starting ...");
            String lambdaFunc = getGardenerApiLambdaFunctionName();
            LOG.info("Use lambda function: "+lambdaFunc);

            port(80);

            /**
             * Health check
             */
            get("/health", (req, res) -> "OK");

            /**
             * API for GardenKeeper to ask for status of Farm.
             */
            get("/farm/:farmName/:az/state/desired", (req, res) -> {

                try {
                    LOG.info("GET /farm/:farmName/:az/state/desired");
                    res.type("application/json");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    String farmName = req.params(":farmName");
                    String az = req.params(":az");

                    //Switch to GSon to build object.
                    JsonObject lambdaEvent = new JsonObject();
                    lambdaEvent.addProperty("farmName", farmName);
                    lambdaEvent.addProperty("az", az);
                    lambdaEvent.addProperty("api-handler", "get-state");

                    String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();
                    InvokeRequest lambdaReq = new InvokeRequest()
                            .withFunctionName(gardenerApiLambdaFunctionName)
                            .withPayload(lambdaEvent.toString());

                    //Or just forward this to Lambda function.
                    AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                    AWSLambda client = builder.build();

                    LOG.fine("Invoking lambda with: "+lambdaEvent.toString());

                    InvokeResult result = client.invoke(lambdaReq);
                    LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                    if (lambdaResultPayload.isError()) {

                        LOG.severe("Route returning error.");

                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                lambdaResultPayload.getPayloadString()));
                    }

                    String p = "";
                    String payload = lambdaResultPayload.getPayloadString();

                    p = payload.replace("\\\"", "\"");
                    try {
                        p = p.trim();
                        if (p.endsWith("\"")) {
                            p = p.substring(0, p.length() - 1);
                        }
                        if (p.startsWith("\"")) {
                            p = p.substring(1);
                        }

                        LOG.fine("DEBUG: payload after...\n" + p);

                        JsonElement data = new Gson().fromJson(p, JsonElement.class);

                        LOG.info("response (data.toString) = _"+data.toString()+"_");
                        return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS, data));
                    } catch (Exception e) {
                        LOG.severe("p = " + p);
                        LOG.severe("Error: " + e.getMessage());
                        e.printStackTrace();
                        throw e;
                    }

                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });


            /*
              API call for GardenKeeper to report status back to Gardener
             */
            post("/farm/:farmName/:az/state/reported", (req, res) -> {

                try {
                    LOG.info("POST /farm/:farmName/:az/state/reported");
                    res.type("application/json");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    //Record the status of this AZ in the farm.
                    AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                    AWSLambda client = builder.build();

                    String farmName = req.params(":farmName");
                    String az = req.params(":az");

                    //api-handler=report-state
                    JsonObject lambdaEvent = new JsonObject();
                    lambdaEvent.addProperty("farmName", farmName);
                    lambdaEvent.addProperty("az", az);
                    lambdaEvent.addProperty("api-handler", "report-state");

                    String jsonString = req.body();
                    lambdaEvent.addProperty("state", jsonString);

                    String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();
                    InvokeRequest lambdaReq = new InvokeRequest()
                            .withFunctionName(gardenerApiLambdaFunctionName)
                            .withPayload(lambdaEvent.toString());

                    InvokeResult result = client.invoke(lambdaReq);
                    LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                    if (lambdaResultPayload.isError()) {
                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                lambdaResultPayload.getPayloadString()));
                    }

                    LOG.info("response = SUCCESS");
                    return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS));
                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });


            /*
              API call to deploy services to Farm.
              HTTP POST accepts YAML, converts to JSON and then updates the database.
             */
            post("/farm/:farmName/service/:service/:version", (req, res) -> {

                try{
                    LOG.info("POST /farm/:farmName/service/:service/:version");
                    res.type("application/json");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    //Note... lets push the YAML to JSON conversion into Lambda/python.
                    //Or just forward this to Lambda function.
                    AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                    AWSLambda client = builder.build();

                    String farmName = req.params(":farmName");
                    String service = req.params(":service");

                    boolean hasRokuFarmDeployHeaders = false;
                    String rokuFarmVersionString = "";
                    String rokuFarmRepoUrl = "";
                    String rokuFarmUserName = "";
                    String rokuFarmTargetRegion = "all";
                    try{
                        rokuFarmVersionString = req.params(":version");
                        //rokuFarmVerionString = req.headers("X-Roku-Farm-Deploy-Version");
                        rokuFarmRepoUrl = req.headers("X-Roku-Farm-Deploy-Repo-Url");
                        hasRokuFarmDeployHeaders = true;
                        rokuFarmUserName = req.headers("X-Roku-Farm-User-Name");
                        String xRokuTargetRegionHeader = req.headers("X-Roku-Farm-Target-Region");
                        if( xRokuTargetRegionHeader != null && !xRokuTargetRegionHeader.isEmpty() ) {
                            rokuFarmTargetRegion = xRokuTargetRegionHeader;
                        }
                    }catch(Exception e){
                        LOG.log(Level.SEVERE,"Failed to find Roku-Farm deploy headers. message="+e.getMessage(), e);
                    }

                    String serviceJson = getServiceInfoJsonFromFarmBuildVersionTable(service, rokuFarmVersionString);
                    if( serviceJson.isEmpty()) {
                        String errMsg = "Could not find serviceInfo JSON in database.  Service: _"+service+
                                "_ version: _"+rokuFarmVersionString+"_";
                        LOG.warning(errMsg);
                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, errMsg));
                    }

                    LOG.info("Adding service: "+service+" to farm: "+farmName);
                    LOG.fine(serviceJson);

                    JsonObject lambdaEvent = new JsonObject();
                    lambdaEvent.addProperty("farmName", farmName);
                    lambdaEvent.addProperty("service", service);
                    lambdaEvent.addProperty("api-handler", "update-service");
                    lambdaEvent.addProperty("service-json", serviceJson);
                    lambdaEvent.addProperty("targetRegion", rokuFarmTargetRegion);

                    //ToDo: remove this check it is no longer optional with new deployment method.
                    if (hasRokuFarmDeployHeaders==true) {
                        lambdaEvent.addProperty("versionString", rokuFarmVersionString);
                        lambdaEvent.addProperty("repoUrl", rokuFarmRepoUrl);

                        LOG.info("Found RokuFarm deploy headers: "+rokuFarmVersionString
                                +" repo: "+rokuFarmRepoUrl);
                    }else{
                        LOG.info("WARN: No RokuFarm deploy headers");
                    }

                    if (rokuFarmUserName!=null) {
                        lambdaEvent.addProperty("user", rokuFarmUserName);
                    }else{
                        LOG.warning("WARN: No user name");
                    }

                    String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();
                    InvokeRequest lambdaReq = new InvokeRequest()
                            .withFunctionName(gardenerApiLambdaFunctionName)
                            .withPayload(lambdaEvent.toString());

                    InvokeResult result = client.invoke(lambdaReq);
                    LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                    if (lambdaResultPayload.isError()) {
                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                lambdaResultPayload.getPayloadString()));
                    }

                    LOG.info("response = SUCCESS");
                    return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS));

                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });

            /**
             *
             */
            put("/farm/:farmName/service/:service/mode/:mode", (req, res) -> {

                try{
                    LOG.info("PUT /farm/:farmName/service/:service/mode/:mode");
                    res.type("application/json");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    //Note... lets push the YAML to JSON conversion into Lambda/python.
                    //Or just forward this to Lambda function.
                    AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                    AWSLambda client = builder.build();

                    String farmName = req.params(":farmName");
                    String service = req.params(":service");
                    String mode = req.params(":mode");

                    LOG.info("Changing service mode to: "+mode+" for: "+service+" farm: "+farmName);

                    String rokuFarmUserName = "";
                    try{
                        rokuFarmUserName = req.headers("X-Roku-Farm-User-Name");
                    }catch(Exception e){
                        LOG.log(Level.SEVERE,"Failed to find Roku-Farm deploy headers. message="+e.getMessage(), e);
                    }

                    JsonObject lambdaEvent = new JsonObject();
                    lambdaEvent.addProperty("farmName", farmName);
                    lambdaEvent.addProperty("service", service);
                    lambdaEvent.addProperty("mode", mode);
                    lambdaEvent.addProperty("api-handler", "change-service-mode");
                    if(rokuFarmUserName!=null){
                        lambdaEvent.addProperty("user", rokuFarmUserName);
                    }

                    String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();
                    InvokeRequest lambdaReq = new InvokeRequest()
                            .withFunctionName(gardenerApiLambdaFunctionName)
                            .withPayload(lambdaEvent.toString());

                    InvokeResult result = client.invoke(lambdaReq);
                    LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                    if (lambdaResultPayload.isError()==true) {
                        LOG.info("put mode error.");
                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                lambdaResultPayload.getPayloadString()));
                    }

                    LOG.info("response = SUCCESS");
                    return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS));

                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });


            /**
             * Delete the named service.
             */
            delete("/farm/:farmName/service/:service", (req, res) -> {
                try{
                    LOG.info("DELETE /farm/:farmName/service/:service");
                    res.type("application/json");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                    AWSLambda client = builder.build();

                    String farmName = req.params(":farmName");
                    String service = req.params(":service");

                    LOG.info("Removing service: "+service+" to farm: "+farmName);

                    String rokuFarmUserName = "";
                    try{
                        rokuFarmUserName = req.headers("X-Roku-Farm-User-Name");
                    }catch(Exception e){
                        LOG.log(Level.SEVERE,"Failed to find Roku-Farm deploy headers. message="+e.getMessage(), e);
                    }

                    JsonObject lambdaEvent = new JsonObject();
                    lambdaEvent.addProperty("farmName", farmName);
                    lambdaEvent.addProperty("service", service);
                    lambdaEvent.addProperty("api-handler", "delete-service");
                    if(rokuFarmUserName!=null){
                        lambdaEvent.addProperty("user", rokuFarmUserName);
                    }

                    String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();
                    InvokeRequest lambdaReq = new InvokeRequest()
                            .withFunctionName(gardenerApiLambdaFunctionName)
                            .withPayload(lambdaEvent.toString());

                    InvokeResult result = client.invoke(lambdaReq);
                    LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                    if (lambdaResultPayload.isError()) {
                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                lambdaResultPayload.getPayloadString()));
                    }

                    LOG.info("response = SUCCESS");
                    return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS));

                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });

            /**
             * Get inspection results for the farm.
             */
            get("/farm/:farmName/inspect", (req, res) -> {
                try{
                    LOG.info("GET /farm/:farmName/inspect");
                    res.type("application/json");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                    AWSLambda client = builder.build();

                    String farmName = req.params(":farmName");

                    LOG.info("Inspect farm. farm: "+farmName);
                    JsonObject lambdaEvent = new JsonObject();
                    lambdaEvent.addProperty("farmName", farmName);
                    lambdaEvent.addProperty("api-handler", "get-farm-inspect");

                    String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();
                    InvokeRequest lambdaReq = new InvokeRequest()
                            .withFunctionName(gardenerApiLambdaFunctionName)
                            .withPayload(lambdaEvent.toString());

                    InvokeResult result = client.invoke(lambdaReq);
                    LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                    if (lambdaResultPayload.isError()) {
                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                lambdaResultPayload.getPayloadString()));
                    }

                    LOG.info("response = _"+lambdaResultPayload.getPayloadString()+"_");
                    return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS,
                            lambdaResultPayload.getPayloadString()));

                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });

            /*
              Get the details of a service.
             */
            get("/farm/:farmName/service/:service/desired", (req, res) -> {

                try{
                    LOG.info("GET /farm/:farmName/service/:service/desired");
                    res.type("application/json");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                    AWSLambda client = builder.build();

                    String farmName = req.params(":farmName");
                    String service = req.params(":service");

                    LOG.info("Get Service desired state. service: "+service+" to farm: "+farmName);

                    JsonObject lambdaEvent = new JsonObject();
                    lambdaEvent.addProperty("farmName", farmName);
                    lambdaEvent.addProperty("service", service);
                    lambdaEvent.addProperty("api-handler", "get-service-desired-state");

                    String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();
                    InvokeRequest lambdaReq = new InvokeRequest()
                            .withFunctionName(gardenerApiLambdaFunctionName)
                            .withPayload(lambdaEvent.toString());

                    InvokeResult result = client.invoke(lambdaReq);
                    LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                    if (lambdaResultPayload.isError()) {
                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                lambdaResultPayload.getPayloadString()));
                    }

                    String p = "";
                    String payload = lambdaResultPayload.getPayloadString();

                    LOG.info("payload=\n"+payload);

                    try {
                        p = payload;
                        LOG.info("DEBUG: payload after...\n" + p);

                        JsonElement data = new Gson().fromJson(p, JsonElement.class);

                        // Move stateMap to state in JSON Object.
                        JsonElement stateMapObj = data.getAsJsonObject().get("stateMap");
                        if(stateMapObj!=null) {
                            data.getAsJsonObject().remove("state");
                            data.getAsJsonObject().add("state", stateMapObj);
                            data.getAsJsonObject().remove("stateMap");
                        }

                        //remove serviceJson (enconding) if it is there.
                        JsonElement serviceJsonObj = data.getAsJsonObject().get("serviceJson");
                        if(serviceJsonObj!=null){
                            data.getAsJsonObject().remove("serviceJson");
                        }

                        LOG.info("response = _"+data+"_");
                        return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS, data));
                    } catch (Exception e) {
                        LOG.severe("p = " + p);
                        LOG.severe("Error: " + e.getMessage());
                        e.printStackTrace();
                        throw e;
                    }

                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });

            /*
              Build scripts calls this Gardener API to post the location of the
              YAML files and to get a valid version string from Gardener.
             */
            post("/service/:service/build", (req, res) -> {

                try{

                    LOG.info("POST /service/:service/build");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    try {
                        res.type("application/json");

                        String service = req.params(":service");
                        LOG.info("POST /service/"+service+"/build");

                        //Per CTDEVOPS-706
                        String shortGitHash = req.headers("X-Roku-Short-Git-Hash");
                        String dockerRepoUrl = req.headers("X-Roku-Docker-Repo-Url");
                        String buildUser = req.headers("X-Roku-Build-User");
                        String buildBranch = req.headers("X-Roku-Build-Branch");

                        String serviceYaml = req.body();
                        LOG.info("DEBUG: POST Body expect YAML \n_"+serviceYaml+"_");
                        String json = Yaml2JsonUntil.convertYamlToJson(serviceYaml);
                        LOG.info("YAML has been converted to JSON: \n_"+json+"_\n");

                        //Check JSON for required keys per: CTDEVOPS-585
                        if( !hasRequiredKeys(json) ){
                            StringBuilder errMsg = new StringBuilder("ERROR: SeedInfo file keys.");
                            List<String> missingKeys = getMissingRequiredKeys(json);
                            if( missingKeys.size()>0 ) {
                                errMsg.append(" Missing keys: ");
                                errMsg.append(String.join(",", missingKeys));
                                errMsg.append(".");
                            }
                            List<String> restrictedKey = listRestrictedKeysIfPresent(json);
                            if( restrictedKey.size()>0 ) {
                                errMsg.append(" Restricted keys: ");
                                errMsg.append(String.join(",", restrictedKey));
                                errMsg.append(".");
                            }

                            LOG.warning(errMsg.toString());
                            return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, errMsg.toString()));
                        }

                        String jsonBase64Encoded = Base64.getEncoder().encodeToString(json.getBytes());

                        LOG.info("Build service: "+service+" shortGitHash: "+shortGitHash);
                        LOG.info("jsonBase64Encoded = "+jsonBase64Encoded);

                        JsonObject lambdaEvent = new JsonObject();
                        lambdaEvent.addProperty("service", service);
                        lambdaEvent.addProperty("serviceJsonBase64", jsonBase64Encoded);
                        lambdaEvent.addProperty("shortGitHash", shortGitHash);
                        lambdaEvent.addProperty("dockerRepoUrl", dockerRepoUrl);
                        lambdaEvent.addProperty("buildUser", buildUser);
                        if(buildBranch.length()>1){
                            lambdaEvent.addProperty("buildBranch", buildBranch);
                        }

                        lambdaEvent.addProperty("api-handler", "post-service-build-info");

                        String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();

                        LOG.info("Invoke lambda: "+gardenerApiLambdaFunctionName);

                        InvokeRequest lambdaReq = new InvokeRequest()
                                .withFunctionName(gardenerApiLambdaFunctionName)
                                .withPayload(lambdaEvent.toString());

                        AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                        AWSLambda client = builder.build();

                        InvokeResult result = client.invoke(lambdaReq);
                        LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                        if (lambdaResultPayload.isError()) {
                            return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                    lambdaResultPayload.getPayloadString()));
                        }

                        String payload = lambdaResultPayload.getPayloadString();
                        if (payload.endsWith("\"")) {
                            payload = payload.substring(0, payload.length() - 1);
                        }
                        if (payload.startsWith("\"")) {
                            payload = payload.substring(1);
                        }

                        LOG.info("response = _"+payload+"_");
                        return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS, payload));
                    }catch (Exception e) {
                        LOG.severe("Error: " + e.getMessage());
                        e.printStackTrace();
                        throw e;
                    }

                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });


            /*
                Get the status of a service in all farms.

                It returns JSON that looks like the following.
             */
            get("/service/:service/status", (req, res) -> {

                try{
                    LOG.info("GET /service/:service/status");
                    res.type("application/json");

                    String authHeader = req.headers("Authorization");
                    //Validate JWT token.
                    if (!verifyJwtToken(authHeader)){
                        return createFailedAuthResponse();
                    }

                    AWSLambdaClientBuilder builder = AWSLambdaClientBuilder.standard();
                    AWSLambda client = builder.build();

                    String service = req.params(":service");

                    LOG.info("Get Service status. service: "+service);

                    JsonObject lambdaEvent = new JsonObject();;
                    lambdaEvent.addProperty("service", service);
                    lambdaEvent.addProperty("api-handler", "get-service-status-everywhere");

                    String gardenerApiLambdaFunctionName = getGardenerApiLambdaFunctionName();
                    InvokeRequest lambdaReq = new InvokeRequest()
                            .withFunctionName(gardenerApiLambdaFunctionName)
                            .withPayload(lambdaEvent.toString());

                    InvokeResult result = client.invoke(lambdaReq);
                    LambdaResultPayload lambdaResultPayload = new LambdaResultPayload(result);
                    if (lambdaResultPayload.isError()) {
                        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                                lambdaResultPayload.getPayloadString()));
                    }

                    String p = "";
                    String payload = lambdaResultPayload.getPayloadString();

                    LOG.info("payload=\n"+payload);

                    try {
                        p = payload;
                        LOG.info("DEBUG: payload after...\n" + p);

                        JsonElement data = new Gson().fromJson(p, JsonElement.class);

                        LOG.info("response = _"+data+"_");
                        return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS, data));
                    } catch (Exception e) {
                        LOG.severe("p = " + p);
                        LOG.severe("Error: " + e.getMessage());
                        e.printStackTrace();
                        throw e;
                    }

                }catch (Exception e){
                    LOG.log(Level.SEVERE,e.getMessage(),e);
                    return new Gson().toJson(new StandardResponse(StatusResponse.ERROR, e.getMessage()));
                }
            });


            //Finished adding routes.

            //create a timer.
            ScheduledExecutorService scheduledExecutorService =
                    Executors.newScheduledThreadPool(1);

            scheduledExecutorService.scheduleAtFixedRate(new Runnable() {
                    public void run() {
                        LOG.fine("exec service running");
                    }
                }, 1, 60, TimeUnit.SECONDS);

            LOG.info("Gardener started...");

            //This is the catch all exception handler
            Spark.exception(Exception.class, (exception, request, response) -> {
                exception.printStackTrace();
            });

        }catch (Exception e){
            LOG.log(Level.SEVERE,e.getMessage(),e);
        }
    }


    /**
     * Verify a JWT token
     * @param authHeader Authorization HTTP header.
     * @return boolean true if verified
     */
    private static boolean verifyJwtToken(String authHeader){
        return verifyJwtToken(authHeader, false);
    }

    /**
     * Checks the Auth header for a JWT token.
     * @param authHeader Authorization HTTP header.
     * @return boolean true if verified
     */
    private static boolean verifyOptionalJwtToken(String authHeader){
        checkUseJwtParam();
        return verifyJwtToken(authHeader, useJwt.get());
    }

    /**
     * Validate the auth token.
     * @param authHeader Authorization HTTP header.
     * @param isTestMode set to true of just test mode
     * @return boolean true if passed. false if failed.
     */
    private static boolean verifyJwtToken(String authHeader, Boolean isTestMode) {

        if(authHeader==null){
            LOG.info("No auth token found.");
            if(isTestMode){ return true; }
            else{ return false; }
        }

        try{
            String token = parseAuthHeader(authHeader);
            Pair<Boolean, Claims> vt = VERIFY.verifyToken(token);

            if(vt.getKey().booleanValue()){
                // Valid token
                return true;
            } else {
                // Invalid token
                LOG.info("Invalid token: "+token);
                if(isTestMode){ return false; }
            }
        }catch (Exception e){
            LOG.log(Level.SEVERE,e.getMessage(),e);
        }
        if(isTestMode){return true;}
        else{return false;}
    }

    /**
     * Check for missing keys in the json output. If found return true.
     * @param json String JSON
     * @return boolean true if required keys are missing.
     */
    private static boolean hasRequiredKeys(String json) {
        boolean isValidJson = true;
        List<String> restrictedKeys = listRestrictedKeysIfPresent(json);
        if( restrictedKeys.size() > 0 ) {
            isValidJson = false;
        }

        List<String> missingKeys = getMissingRequiredKeys(json);
        if( missingKeys.size()>0 ){
            isValidJson = false;
        }

        return isValidJson;
    }

    /**
     * If seed_info JSON has any restricted keys list what they are.
     * In the normal case this should return an empty list.
     * @param json Sting JSON
     * @return List of Strings.  If no restricted keys are found, return an empty list.
     */
    private static List<String> listRestrictedKeysIfPresent(String json) {
        JsonObject rootObj = null;
        List<String> retVal = new ArrayList<>();
        try {
            JsonParser parser = new JsonParser();
            rootObj = parser.parse(json).getAsJsonObject();
        } catch (Exception e) {
            LOG.warning("Invalid JSON: _"+json+"_");
            LOG.warning("Invalid JSON: "+e.getMessage());
            retVal.add("Invalid JSON. error: "+e.getMessage());
            return retVal;
        }
        if( rootObj == null ){
            retVal.add("Invalid JSON");
            return retVal;
        }
        Set<String> keysInRoot = rootObj.keySet();

        //List of restricted keys that cannot be at root of JSON file.
        List<String> restrictedKeysList = Arrays.asList("repo", "version", "state", "target_region");
        Set<String> restrictedKeysAtRoot = new HashSet<>(restrictedKeysList);

        // look for any restricted keys, which is the intersection of JSON and restricted keys list.
        Set<String> intercetionSet = new TreeSet<>(keysInRoot);
        intercetionSet.retainAll(restrictedKeysAtRoot);

        retVal.addAll(intercetionSet);
        return retVal;
    }

    /**
     *
     * @param json string JSON
     * @return String Array with name of missing required keys. If non are
     * missing then returns an array of size zero.
     */
    private static List<String> getMissingRequiredKeys(String json) {
        JsonObject rootObj = null;
        List<String> retVal = new ArrayList<>();
        try {
            JsonParser parser = new JsonParser();
            rootObj = parser.parse(json).getAsJsonObject();
        } catch (Exception e) {
            LOG.warning("Invalid JSON: _"+json+"_");
            LOG.warning("Invalid JSON: "+e.getMessage());
            retVal.add("Invalid JSON. error: "+e.getMessage());
            return retVal;
        }
        if( rootObj == null ){
            retVal.add("Invalid JSON");
            return retVal;
        }
        Set<String> keysInRoot = rootObj.keySet();

        //Required keys are root.
        boolean missingDockerKey = false;

        List<String> requiredKeyList = Arrays.asList("service_name", "target", "docker");
        Set<String> requiredKeysAtRoot = new HashSet<>(requiredKeyList);

        if (!keysInRoot.containsAll(requiredKeysAtRoot)){
            LOG.warning("SeedInfo file is missing some required keys");
            for ( String currKey : requiredKeyList ){
                if( !hasJsonKey(rootObj, currKey)){
                    LOG.warning("Didn't find key: "+currKey);
                    retVal.add(currKey);
                    if (currKey.equalsIgnoreCase("docker")){
                        missingDockerKey = true;
                    }
                }
            }
        }

        //Required keys under docker.
        if( !missingDockerKey ){
            //Look for required docker sub-keys.
            LOG.info("Verify docker keys are present.");
            JsonObject dockerObj = rootObj.getAsJsonObject("docker");
            String[] reqDockerKeyList = new String[] {"cpu", "mem", "ports" };
            for( String currDockerKey : reqDockerKeyList ){
                if( !hasJsonKey(dockerObj, currDockerKey)){
                    retVal.add("docker:"+currDockerKey);
                }
            }
        }

        return retVal;
    }

    /**
     * Verify a key is in the JSON.
     * @param parentObj JsonObject
     * @param key String key name.
     * @return boolean True if the key exists in the JSON.
     */
    private static boolean hasJsonKey( JsonObject parentObj, String key) {
        return parentObj.has(key);
    }

    /**
     * Parse a token header string and return just the token.
     * @param authHeader Authorization HTTP header.
     * @return
     */
    private static String parseAuthHeader(String authHeader) {
        authHeader = authHeader.trim();
        String[] splitted = authHeader.split("\\s+");
        String token = splitted[splitted.length-1];


        //ToDo: log a shorter version of the token.
        String shortToken = shortenString(token);
        LOG.info("token: "+shortToken);

        return token;
    }

    /**
     * Create the standard response to a failed authentication request.
     * @return JSON String
     */
    private static String createFailedAuthResponse(){
        return new Gson().toJson(new StandardResponse(StatusResponse.ERROR,
                "Failed authentication"));
    }

    /**
     * Take a potentially long string like a JWT token and shorten it
     *
     * @param longString Long JWT Token which needs to be obscured and shortened.
     * @return String short JWT token with middle removed.
     */
    private static String shortenString(String longString){

        String shortString = longString;
        int len = longString.length();
        if(len>20) {
            shortString = longString.substring(0,8)+"...(len="+len+")..."+longString.substring(len-15);
        }
        return shortString;
    }

    /**
     * Timestamp in log format.
     * @return String
     */
    private static String getTimestamp() {
        return sdf.format(new Date());
    }

    /**
     * Look for the
     */
    private static void checkUseJwtParam(){
        String value = gpStore.getParam("GARDENER_USE_JWT");
        if(value!=null){
            boolean originalValue = useJwt.get();
            value = value.toLowerCase();
            if(value.startsWith("f")){
                useJwt.getAndSet(false);
                if(originalValue){
                    LOG.warning("Changing GARDENER_USE_JWT from true, to false");
                }
            }else{
                useJwt.getAndSet(true);
                LOG.info("Changing GARDENER_USE_JWT from false, to true");
            }
        }else{
            LOG.log(Level.WARNING,"Param Store key: GARDENER_USE_JWT was null. Using useJwt="+useJwt.get());
        }
    }

    /**
     *
     * @return Name of gardner-api lambda function.
     * Either "gardener-api" for prod
     * or "gardener-api-dev" for dev
     */
    private static String getGardenerApiLambdaFunctionName(){
        String name = tagReader.getNameTag();
        if (name.indexOf("-dev")>0){
            return "gardener-api-dev";
        }else{
            return "gardener-api";
        }
    }

    /**
     * Return the serviceInfo JSON String by looking up the service an version.
     *
     * If not found, return an empty String.
     *
     * @param service String - serviceName like worldview
     * @param rokuFarmVersionString String version string like "2018111-14-1b178b52-master"
     * @return
     */
    private static String getServiceInfoJsonFromFarmBuildVersionTable(String service, String rokuFarmVersionString)
    {
        AmazonDynamoDB client = AmazonDynamoDBClientBuilder.standard().build();
        //DynamoDB dynamoDB = new DynamoDB(client);

        Map.Entry<String, AttributeValue> primaryKey
                = new AbstractMap.SimpleEntry<>("serviceName", new AttributeValue(service));
        Map.Entry<String, AttributeValue> sortKey
                = new AbstractMap.SimpleEntry<>("buildNumber", new AttributeValue(rokuFarmVersionString));

        GetItemRequest request = new GetItemRequest()
                .withTableName("FarmBuildVersion")
                .withKey(primaryKey, sortKey);

        GetItemResult result = client.getItem(request);

        Map<String, AttributeValue> item = result.getItem();

        if(item == null){
            //Indicate that now result was found.
            return "";
        }

        AttributeValue serviceInfo = item.get("serviceInfo");
        String serviceJson = serviceInfo.getS();

        return serviceJson;
    }

}