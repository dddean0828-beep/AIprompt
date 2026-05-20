package com.aiprompt.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("prompt_tag")
public class PromptTag {
    private Long id;
    private Long promptId;
    private Long tagId;
}
