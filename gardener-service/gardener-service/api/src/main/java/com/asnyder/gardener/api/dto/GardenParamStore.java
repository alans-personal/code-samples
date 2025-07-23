package com.asnyder.gardener.api.dto;

import com.amazonaws.services.simplesystemsmanagement.AWSSimpleSystemsManagement;
import com.amazonaws.services.simplesystemsmanagement.AWSSimpleSystemsManagementClient;
import com.amazonaws.services.simplesystemsmanagement.AWSSimpleSystemsManagementClientBuilder;
import com.amazonaws.services.simplesystemsmanagement.model.GetParameterRequest;
import com.amazonaws.services.simplesystemsmanagement.model.GetParameterResult;
import com.asnyder.gardener.api.Main;

import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

public class GardenParamStore {

    private final static Logger LOG = Logger.getLogger(GardenParamStore.class.getName());

    private static GardenParamStore ourInstance = new GardenParamStore();

    public static GardenParamStore getInstance() {
        return ourInstance;
    }

    Map<String, String> keyValueMap = new HashMap<>();
    Map<String, Date> keyLastUpdate = new HashMap<>();

    AWSSimpleSystemsManagement ssmClient;

    private static final long DEFAULT_WAIT_TIME_MILLI_SEC = 60 * 1000; // 60 seconds.

    private GardenParamStore() {
        ssmClient = AWSSimpleSystemsManagementClientBuilder.defaultClient();
    }

    /**
     * Get parameter from param store. But only check once per minute.
     * @param keyName in local region Parameter Store.
     * @return String
     */
    public String getParam(String keyName){

        try {
            boolean callParamStore = false;

            //Does parameter exist?
            if (!keyLastUpdate.containsKey(keyName)) {
                callParamStore = true;
            } else {
                long currTime = System.currentTimeMillis();
                Date lastUpdate = keyLastUpdate.get(keyName);
                long lastUpdateTime = lastUpdate.getTime();

                if (currTime > lastUpdateTime + DEFAULT_WAIT_TIME_MILLI_SEC) {
                    LOG.info("Update param: " + keyName);

                    GetParameterRequest gpReq = new GetParameterRequest();
                    gpReq.setName(keyName);

                    GetParameterResult gpRes = ssmClient.getParameter(gpReq);
                    if (gpRes != null){
                        return gpRes.getParameter().getValue();
                    }
                }
            }
        }catch (Exception ex) {
            LOG.log(Level.SEVERE,"getParam("+keyName+") failed.",ex);
        }
        return null;
    }

}
