package com.asnyder.gardener.api;

import com.google.gson.*;

public class StandardResponse {

    private StatusResponse status;
    private String message;
    private JsonElement data;

    public StandardResponse(StatusResponse status) {
        this.status = status;
    }

    /**
     * Use this for ERROR responses.
     * @param status ERROR
     * @param message String reason for error.
     */
    public StandardResponse(StatusResponse status, String message) {
        this.status = status;
        this.message = message;
        //this.data = new JsonPrimitive(message);
    }

    public StandardResponse(StatusResponse status, JsonElement data) {
        this.status = status;
        this.data = data;
    }

}