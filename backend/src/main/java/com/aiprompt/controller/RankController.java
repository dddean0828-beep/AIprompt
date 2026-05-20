package com.aiprompt.controller;

import com.aiprompt.common.Result;
import com.aiprompt.entity.Prompt;
import com.aiprompt.service.PromptService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/rank")
@RequiredArgsConstructor
public class RankController {
    private final PromptService promptService;

    @GetMapping("/hot")
    public Result<List<Prompt>> hot() {
        return Result.ok(promptService.rankByHot());
    }

    @GetMapping("/favorite")
    public Result<List<Prompt>> favorite() {
        return Result.ok(promptService.rankByFavorite());
    }
}
