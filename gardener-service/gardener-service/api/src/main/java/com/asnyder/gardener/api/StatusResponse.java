package com.asnyder.gardener.api;

public enum StatusResponse {
    SUCCESS ("Success"),
    ERROR ("Error");

    private String status;

    StatusResponse(String status) {
        this.status = status;
    }
}