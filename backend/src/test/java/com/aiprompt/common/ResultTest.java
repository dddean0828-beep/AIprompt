package com.aiprompt.common;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class ResultTest {

    @Test
    @DisplayName("ok(data) 应返回 code=200 且携带 data")
    void okWithData() {
        Result<String> r = Result.ok("hello");
        assertThat(r.getCode()).isEqualTo(200);
        assertThat(r.getMessage()).isEqualTo("success");
        assertThat(r.getData()).isEqualTo("hello");
    }

    @Test
    @DisplayName("ok(message, data) 应使用自定义 message")
    void okWithMessageAndData() {
        Result<Integer> r = Result.ok("done", 42);
        assertThat(r.getCode()).isEqualTo(200);
        assertThat(r.getMessage()).isEqualTo("done");
        assertThat(r.getData()).isEqualTo(42);
    }

    @Test
    @DisplayName("fail 应返回 code=500 且 data 为 null")
    void failMessage() {
        Result<Object> r = Result.fail("error");
        assertThat(r.getCode()).isEqualTo(500);
        assertThat(r.getMessage()).isEqualTo("error");
        assertThat(r.getData()).isNull();
    }
}
