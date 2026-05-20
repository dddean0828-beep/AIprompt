package com.aiprompt.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("prompt")
public class Prompt {
    private Long id;
    private String title;
    private String content;
    private String category;
    private Long creatorId;
    private String creatorName;
    private Integer isPrivate;
    private Integer useCount;
    private Integer favoriteCount;
    private LocalDateTime createdAt;
}
