package com.aiprompt.dto;

import com.aiprompt.entity.Prompt;
import lombok.Data;

@Data
public class FavoritePromptVO {
    private Long favoriteId;
    private Prompt prompt;
}
