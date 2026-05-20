package com.aiprompt.controller;

import com.aiprompt.common.Result;
import com.aiprompt.dto.FavoritePromptVO;
import com.aiprompt.dto.FavoriteRequest;
import com.aiprompt.service.InteractionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/favorite")
@RequiredArgsConstructor
public class FavoriteController {
    private final InteractionService interactionService;

    @PostMapping("/add")
    public Result<Boolean> add(@RequestBody FavoriteRequest request) {
        return Result.ok(interactionService.addFavorite(request.getUserId(), request.getPromptId()));
    }

    @DeleteMapping("/remove/{id}")
    public Result<Boolean> remove(@PathVariable Long id) {
        return Result.ok(interactionService.removeFavorite(id));
    }

    @GetMapping("/list")
    public Result<List<FavoritePromptVO>> list(@RequestParam Long userId) {
        return Result.ok(interactionService.favoriteList(userId));
    }
}
