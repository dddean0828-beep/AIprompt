package com.aiprompt.utils;

import io.jsonwebtoken.Claims;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class JwtUtilsTest {

    @Test
    @DisplayName("createToken 与 parseToken 应能往返解析 userId 与 username")
    void createAndParseToken() {
        String token = JwtUtils.createToken(100L, "testUser");
        Claims claims = JwtUtils.parseToken(token);
        assertThat(claims.get("userId", Number.class).longValue()).isEqualTo(100L);
        assertThat(claims.get("username", String.class)).isEqualTo("testUser");
        assertThat(claims.getExpiration()).isNotNull();
    }

    @Test
    @DisplayName("非法 token 解析应抛出异常")
    void parseInvalidTokenThrows() {
        assertThatThrownBy(() -> JwtUtils.parseToken("not-a-jwt"))
                .isInstanceOf(Exception.class);
    }
}
