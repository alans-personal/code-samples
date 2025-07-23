package com.asnyder.gardener.api.dto;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ServiceState {
    public String service_name;
    public String host_name;
    public String label;
    public String version;
    public String repo;
    public String state;
    public String target;
    public Integer min_count;
    private Map<String, Object> docker;
    private List<String> public_apis;

    public void addDockerParam(String key, String value){
        if (docker==null){
            docker = new HashMap<>();
        }
        docker.put(key, value);
    }

    public void addDockerParam(String key, Integer value){
        if (docker==null){
            docker = new HashMap<>();
        }
        docker.put(key, value);
    }

    public void addDockerParam(String key, List<String> value){
        if (docker==null){
            docker = new HashMap<>();
        }
        docker.put(key, value);
    }

    public void addDockerEnvVariable(String key, String value){
        if (docker==null){
            docker = new HashMap<>();
        }

        Object environment = docker.get("environment");
        if (environment == null){
            environment = new ArrayList<Map<String,String>>();
            docker.put("environment", environment);
        }
        if (!(environment instanceof ArrayList<?>)) {
            String msg = "Docker 'environment' key expected type: ArrayList<?>. Was type: "+environment.getClass();
            throw new IllegalArgumentException(msg);
        }

        //add a new map into the array.
        Map<String, String> envItem = new HashMap<>();
        envItem.put(key, value);
        ((ArrayList) environment).add(envItem);
    }

    public void addPublicApi(String pathExpression) {
        if (public_apis==null){
            public_apis = new ArrayList<String>();
        }
        public_apis.add(pathExpression);
    }
}
