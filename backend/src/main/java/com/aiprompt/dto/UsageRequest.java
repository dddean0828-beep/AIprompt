package com.aiprompt.dto;

import lombok.Data;

@Data
public class UsageRequest {
    private Long userId;
    private Long promptId;
}
