package com.asnyder.gardener.api.mock;

import com.asnyder.gardener.api.dto.DesiredState;
import com.asnyder.gardener.api.dto.ServiceState;

import java.util.ArrayList;
import java.util.List;

public class MockUtil {

    private MockUtil(){}

    public static DesiredState mockDesiredState() {

//        ServiceState tfpodState = makeTfPod();
//        ServiceState lsState = makeLocationService();
//
//        DesiredState desiredState = new DesiredState();
//        desiredState.add(tfpodState);
//        desiredState.add(lsState);

        //This for demo.
        ServiceState perfBeanState = makeDemoPerfBean();
        ServiceState lsState = makeDemoLocationService();

        DesiredState desiredState = new DesiredState();
        desiredState.add(lsState);
        desiredState.add(perfBeanState);

        return desiredState;
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

    static ServiceState makeDemoPerfBean() {
        ServiceState perfBeanState = new ServiceState();
        perfBeanState.service_name = "perfbean";
        perfBeanState.host_name = "perfbean";
        perfBeanState.label = "115465-b93dad1"; // <-- Is this needed? Likely not.
        perfBeanState.version = "sre34c2-20180622-42"; // <-- Needed but needs database row to cross reference.
        perfBeanState.repo = "docker-dev.artifactory.tools.asnyder.com/devops/tf-farm/perfbean:132638-d15420d";
        perfBeanState.state = "run";
        perfBeanState.target = "general";
        perfBeanState.min_count = 1;

        perfBeanState.addDockerParam("cpu", 128);
        perfBeanState.addDockerParam("mem", "256mb");
        List<String> portList = new ArrayList<>();
        portList.add("8000");
        perfBeanState.addDockerParam("ports",portList);
        perfBeanState.addDockerParam("nofile", 32000);
        perfBeanState.addDockerParam("awslogs-group", "perfbean-development");
        perfBeanState.addDockerParam("awslogs-region","us-west-2");
        perfBeanState.addDockerParam("health_check","/perfbean/healthcheck");
        perfBeanState.addDockerParam("auth","none");

        return perfBeanState;        
    }

    static ServiceState makeDemoLocationService() {
        ServiceState lsState = new ServiceState();
        lsState.service_name = "ls";
        lsState.host_name = "ls";
        lsState.label = "115465-b93dad1"; // <- Not sure if needed.
        lsState.version = "v2"; // <- this should confirm to a different format.
        lsState.repo = "docker-dev.artifactory.tools.asnyder.com/cti/location-service-app:115465-b93dad1";
        lsState.state = "run";
        lsState.target = "general";
        lsState.min_count = 1;

        lsState.addDockerParam("cpu", 1024);
        lsState.addDockerParam("mem", "500mb");
        List<String> portList = new ArrayList<>();
        portList.add("8080");
        lsState.addDockerParam("ports",portList);
        lsState.addDockerParam("nofile", 64008);
        lsState.addDockerParam("awslogs-group", "ls-development");
        lsState.addDockerParam("awslogs-region","us-west-2");
        lsState.addDockerParam("health_check","/health");
        lsState.addDockerParam("auth","JWT");

        lsState.addDockerEnvVariable("RK_CONFIG_S3_BUCKET", "v1.dev.ls.service.config.ctidev.asnyder.com");
        lsState.addDockerEnvVariable("RK_CONFIG_S3_REGION", "us-east-1");
        lsState.addDockerEnvVariable("RK_ENV_NAME", "development");
        lsState.addDockerEnvVariable("RK_SERVICE_ENV", "development");

        return lsState;
    }

//    /**
//     *
//     * @param args
//     */
//    public static void main(String[] args) {
//                return new Gson().toJson(new StandardResponse(StatusResponse.SUCCESS,
//                        new Gson().toJsonTree(mockDesiredState)));
//    }

}
