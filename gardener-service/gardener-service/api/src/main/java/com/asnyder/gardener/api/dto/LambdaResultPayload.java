package com.asnyder.gardener.api.dto;

import com.amazonaws.services.dynamodbv2.xspec.S;
import com.amazonaws.services.lambda.model.InvokeResult;
import com.asnyder.gardener.api.Main;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

/**
 * Payload of a lambda result.
 *
 * If ERROR, it gives the message.
 * Otherwise it gives the payload as a string.
 *
 */
public class LambdaResultPayload {

    private final static Logger LOG = LoggerFactory.getLogger(LambdaResultPayload.class);

    boolean isError;
    String payloadString;

    public LambdaResultPayload(InvokeResult result){

        try {
            isError = false;
            ByteBuffer payloadBytes = result.getPayload();
            String payload = StandardCharsets.UTF_8.decode(payloadBytes).toString();

            String checkForError = payload.toUpperCase();
            checkForError = checkForError.replace("\"","");
            checkForError = checkForError.replace("'", "");
            checkForError = checkForError.trim();

            if (checkForError.startsWith("ERROR")){
                isError = true;
            } else if (checkForError.startsWith("FAIL")) {
                isError = true;
            }

            if(isError) {
                LOG.warn("Error: payload="+payload);
            } else {
                LOG.info("payload: "+payload);
            }

            payloadString = payload;
        }catch (Exception e){
                isError = true;
                payloadString = "Failed to parse payload. Reason: "+e.getMessage();
                e.printStackTrace();
        }
    }

    public boolean isError(){
        LOG.debug("isError="+isError);
        return isError;
    }

    public String getPayloadString(){ return payloadString; }

}
