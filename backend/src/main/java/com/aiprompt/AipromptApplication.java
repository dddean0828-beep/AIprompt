package com.aiprompt;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.aiprompt.mapper")
public class AipromptApplication {
    public static void main(String[] args) {
        SpringApplication.run(AipromptApplication.class, args);
    }
}
