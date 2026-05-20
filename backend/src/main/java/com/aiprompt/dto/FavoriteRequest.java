package com.aiprompt.dto;

import lombok.Data;

@Data
public class FavoriteRequest {
    private Long userId;
    private Long promptId;
}
