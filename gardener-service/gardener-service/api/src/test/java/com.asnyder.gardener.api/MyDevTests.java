package com.asnyder.gardener.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.asnyder.gardener.api.dto.DesiredState;
import com.asnyder.gardener.api.dto.ServiceState;
import com.asnyder.gardener.api.mock.MockUtil;

import java.util.ArrayList;
import java.util.List;


public class MyDevTests {

    public static void main(String[] args) {

        //testJsonFormatting();
        testJsonFormatting2();

//        testErrorResponse();
//        printMockService();

    }

    static void testErrorResponse() {

        System.out.println("\nShow error response.\n");

        Gson gson1 = new GsonBuilder().setPrettyPrinting().create();

        String jsonOutput = gson1.toJson(new StandardResponse(
                StatusResponse.ERROR, "Something went horribly wrong."));

        System.out.println(jsonOutput);

        System.out.println("\n----------------\n");
    }

    static void testJsonFormatting2() {

        try {
            System.out.println("\n--- Start ---\n");
            String textStr = "{ \"services\": [{\"service_name\":\"ls\",\"host_name\":\"ls\",\"label\":\"115465-b93dad1\",\"version\":\"v2\",\"repo\":\"docker-dev.artifactory.tools.asnyder.com/cti/location-service-app:115465-b93dad1\",\"state\":\"run\",\"target\":\"general\",\"min_count\":1,\"docker\":{\"awslogs-group\":\"ls-development\",\"environment\":[{\"RK_CONFIG_S3_BUCKET\":\"v1.dev.ls.service.config.ctidev.asnyder.com\"},{\"RK_CONFIG_S3_REGION\":\"us-east-1\"},{\"RK_ENV_NAME\":\"development\"},{\"RK_SERVICE_ENV\":\"development\"}],\"mem\":\"500mb\",\"auth\":\"JWT\",\"awslogs-region\":\"us-west-2\",\"cpu\":1024,\"ports\":[\"8080\"],\"nofile\":64008,\"health_check\":\"/health\"}}] }";
            System.out.println("textStr = " + textStr);
            JsonElement data = new Gson().fromJson(textStr, JsonElement.class);

            System.out.println("data = "+data.toString());

            String ret_val = new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS, data));
            System.out.println("ret_val = "+ret_val);

            System.out.println("\n--- End ---\n");
        } catch (Exception e) {
            System.out.println("\n--- Error ---\n");
            System.out.println("Error: "+e.getMessage());
        }

    }

    //Some quick tests of using gson to format responses.
    static void testJsonFormatting() {

        System.out.println("\nStarting test formatting\n");

        //Here we are going to build up two quick services.
        ServiceState tfpodState = makeTfPod();
        ServiceState lsState = makeLocationService();

        DesiredState desiredState = new DesiredState();
        desiredState.add(tfpodState);
        desiredState.add(lsState);

        Gson gson1 = new GsonBuilder().setPrettyPrinting().create();
        Gson gson2 = new GsonBuilder().setPrettyPrinting().create();

        gson1.toJson(new StandardResponse(StatusResponse.SUCCESS,
                gson2.toJsonTree(desiredState)));

        String jsonOutput = gson1.toJson(
                new StandardResponse(StatusResponse.SUCCESS,
                gson2.toJsonTree(desiredState)));

        System.out.println(jsonOutput);

        System.out.println("\n----------------\n");
    }

    static void printMockService() {

        System.out.println("\n-------- Start --------\n");

        DesiredState desiredState = MockUtil.mockDesiredState();

        Gson gson1 = new GsonBuilder().setPrettyPrinting().create();
        Gson gson2 = new GsonBuilder().setPrettyPrinting().create();

        String jsonOutput = gson1.toJson(gson2.toJsonTree(desiredState));
        System.out.println(jsonOutput);

        System.out.println("\n--------  End  --------\n");
    }

    static ServiceState makeTfPod() {
        ServiceState tfpodState = new ServiceState();
        tfpodState.service_name = "tf-pod";
        tfpodState.host_name = "tfpod";
        tfpodState.label = "115323-0245963";
        tfpodState.version = "ddba79da-20180509-2";
        tfpodState.repo = "docker-dev.artifactory.tools.asnyder.com/devops/tf-pod:115323-0245963";
        tfpodState.state = "run";
        tfpodState.target = "cpu";
        tfpodState.min_count = 2;

        tfpodState.addDockerParam("cpu", 512);
        tfpodState.addDockerParam("mem", "128mb");
        List<String> portList = new ArrayList<>();
        portList.add("8000");
        portList.add("8001");
        tfpodState.addDockerParam("ports",portList);
        tfpodState.addDockerParam("awslogs-group", "tf-pod-development");
        tfpodState.addDockerParam("awslogs-region","us-west-2");
        tfpodState.addDockerParam("health_check","/health");
        tfpodState.addDockerParam("auth","jwt");

        tfpodState.addDockerEnvVariable("RK_CONFIG_S3_BUCKET", "v1.dev.ls.service.config.ctidev.asnyder.com");
        tfpodState.addDockerEnvVariable("X_SERVICE_8000_CHECK_HTTP", "/perfbean/healthcheck");
        tfpodState.addDockerEnvVariable("X_SERVICE_8000_NAME", "perfbean");
        tfpodState.addDockerEnvVariable("X_SERVICE_CHECK_INTERVAL", "10s");
        tfpodState.addDockerEnvVariable("X_SERVICE_TAGS", "qwertyuiopasdfghjklzxcvbnm1234567890qwertyuiopasdfghjklzxcvbnm1234567890");

        return tfpodState;
    }

    static ServiceState makeLocationService() {
        ServiceState lsState = new ServiceState();
        lsState.service_name = "ls-go";
        lsState.host_name = "ls";
        lsState.label = "115465-b93dad1";
        lsState.version = "sre34c2-20180622-42";
        lsState.repo = "docker-dev.artifactory.tools.asnyder.com/cti/location-service-app:115465-b93dad1";
        lsState.state = "run";
        lsState.target = "memory";
        lsState.min_count = 1;

        lsState.addDockerParam("cpu", 1024);
        lsState.addDockerParam("mem", "500mb");
        List<String> portList = new ArrayList<>();
        portList.add("8000");
        lsState.addDockerParam("ports",portList);
        lsState.addDockerParam("awslogs-group", "ls-development");
        lsState.addDockerParam("awslogs-region","us-west-2");
        lsState.addDockerParam("health_check","/health");
        lsState.addDockerParam("auth","jwt");

        lsState.addDockerEnvVariable("RK_CONFIG_S3_BUCKET", "v1.dev.ls.service.config.ctidev.asnyder.com");

        return lsState;
    }

}
