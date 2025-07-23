package com.asnyder.gardener.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.google.gson.Gson;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;

public class Yaml2JsonUntil {

    private final static Logger LOG = LoggerFactory.getLogger(Yaml2JsonUntil.class);

    private Yaml2JsonUntil(){}

    /**
     * Import YAML and export JSON.
     * @param yaml
     * @return
     * @throws IOException
     */
    public static String convertYamlToJson(String yaml)
            throws IOException
    {
        ObjectMapper yamlReader = new ObjectMapper(new YAMLFactory());
        Object obj = yamlReader.readValue(yaml, Object.class);

        ObjectMapper jsonWriter = new ObjectMapper();
        return jsonWriter.writeValueAsString(obj);
    }

    /**
     *
     * @param ulgyJsonString
     * @return
     */
    public static String prettyPrintJson(String ulgyJsonString) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(ulgyJsonString);
        } catch (Exception e) {
            //Get the first 20 characters.
            String snip = ulgyJsonString.substring(0, 20);
            throw new IllegalArgumentException("String doens't seem to be JSON. Part of string: "+snip+"...");
        }
    }

    public static void main(String[] args) {

        testJsonResponses();

        testYamlToJsonConversion();

    }

    private static void testJsonResponses(){
        try {

            StandardResponse sr1 = new StandardResponse(StatusResponse.SUCCESS, "Look for inner quotes");
            System.out.println( new Gson().toJson(sr1) );

        } catch (Exception e) {
            LOG.error("Error: "+e.toString());
        }
    }

    private static void testYamlToJsonConversion(){
        try {
            String yaml = exampleYaml1();
            String json1 = Yaml2JsonUntil.convertYamlToJson(yaml);

            LOG.debug(json1);

        } catch (Exception e) {
            LOG.error("Error: "+e.toString());
        }
    }

    /**
     * Use case one for testing conversion.
     * @return
     */
    static String exampleYaml1() {
        String yaml = "version: 0.2\n" +
                "\n" +
                "phases:\n" +
                "  install:\n" +
                "    commands:\n" +
                "      - echo COMMANDS phase...\n" +
                "      - pip install awscli --upgrade\n" +
                "      - echo Adding code dependencies for project\n" +
                "      - pip install requests_aws_sign -t ./slack_bud/slack_bud\n" +
                "      - pip install elasticsearch -t ./slack_bud/slack_bud\n" +
                "\n" +
                "  pre_build:\n" +
                "    commands:\n" +
                "      - echo PRE_BUILD phase... verifying state\n" +
                "      - echo `which python`\n" +
                "      - echo `python --version`\n" +
                "      - echo `aws --version`\n" +
                "  build:\n" +
                "    commands:\n" +
                "      - echo BUILD phase...\n" +
                "      - echo Create build_info file.\n" +
                "      - cd ./slack_bud\n" +
                "  post_build:\n" +
                "    commands:\n" +
                "      - echo POST_BUILD phase...\n" +
                "#      - cd ./test\n" +
                "#      - echo `ls`\n" +
                "\n" +
                "artifacts:\n" +
                "  files:\n" +
                "    - '**/*'\n" +
                "  base-directory: slack_bud/slack_bud";

        return yaml;
    }

}
