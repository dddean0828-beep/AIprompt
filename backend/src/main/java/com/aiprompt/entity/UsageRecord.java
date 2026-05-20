package com.aiprompt.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("usage_record")
public class UsageRecord {
    private Long id;
    private Long userId;
    private Long promptId;
    private LocalDateTime createdAt;
}
