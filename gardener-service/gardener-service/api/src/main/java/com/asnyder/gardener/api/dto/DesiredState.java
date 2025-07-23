package com.asnyder.gardener.api.dto;

import java.util.ArrayList;

public class DesiredState {

    ArrayList<ServiceState> services;

    public void add(ServiceState serviceState){
        if (services==null) {
            services = new ArrayList<>();
        }

        services.add(serviceState);
    }

}
