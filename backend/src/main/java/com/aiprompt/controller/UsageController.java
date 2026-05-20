package com.aiprompt.controller;

import com.aiprompt.common.Result;
import com.aiprompt.dto.UsageRequest;
import com.aiprompt.service.InteractionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/usage")
@RequiredArgsConstructor
public class UsageController {
    private final InteractionService interactionService;

    @PostMapping("/add")
    public Result<Boolean> add(@RequestBody UsageRequest request) {
        return Result.ok(interactionService.addUsage(request.getUserId(), request.getPromptId()));
    }
}
