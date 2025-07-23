package com.asnyder.gardener.api.dto;

import java.util.HashMap;
import java.util.Map;

import com.amazonaws.services.ec2.*;
import com.amazonaws.services.ec2.model.*;
import com.amazonaws.util.EC2MetadataUtils;
import com.amazonaws.regions.Regions;

import java.util.logging.*;

public class TagReader {

    private final static Logger LOG = Logger.getLogger(TagReader.class.getName());

    private static TagReader ourInstance = new TagReader();

    public static TagReader getInstance() {
        return ourInstance;
    }

    Map<String, String> cachedTags = new HashMap<>();

    private TagReader() {
        updateCachedTags();
    }


    public void updateCachedTags(){
        cachedTags = readTags();
    }

    public Map<String, String> readTags(){
        Map<String, String> retVal = new HashMap<>();

        String myEc2InstanceId = EC2MetadataUtils.getInstanceId();

        DescribeInstancesRequest request = new DescribeInstancesRequest();
        AmazonEC2 ec2 = AmazonEC2ClientBuilder.standard()
                            .withRegion(Regions.US_WEST_2)
                            .build();

        boolean done = false;
        while(!done) {
            DescribeInstancesResult result = ec2.describeInstances(request);

            for(Reservation reservation : result.getReservations()) {
                for(Instance instance : reservation.getInstances()) {

                    if (myEc2InstanceId.equalsIgnoreCase(instance.getInstanceId())){
                        LOG.info("Found instance: "+myEc2InstanceId);

                        // Get all the tags.
                        if (instance.getTags() != null) {
                            for (Tag tag : instance.getTags()) {
                                retVal.put(tag.getKey(), tag.getValue());
                                LOG.info("found tag: "+tag.getKey()+": "+tag.getValue());
                            }//for
                        }
                    }
                }
            }

            if(result.getNextToken() == null) {
                done = true;
            }
        }

        return retVal;
    }

    /**
     *
     * @return Name tag or empty string.
     */
    public String getNameTag(){
        return getTagByName("Name");
    }

    public String getTagByName(String tagName){
        return cachedTags.getOrDefault(tagName, "");
    }

}
