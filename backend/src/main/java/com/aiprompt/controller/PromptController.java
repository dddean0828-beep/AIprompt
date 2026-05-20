package com.aiprompt.controller;

import com.aiprompt.common.Result;
import com.aiprompt.entity.Prompt;
import com.aiprompt.service.PromptService;
import com.aiprompt.utils.JwtUtils;
import io.jsonwebtoken.Claims;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/prompt")
@RequiredArgsConstructor
public class PromptController {
    private final PromptService promptService;

    @GetMapping("/list")
    public Result<List<Prompt>> list(@RequestParam(required = false) String category,
                                     @RequestParam(required = false) String keyword,
                                     @RequestHeader(value = "Authorization", required = false) String authorization) {
        Long currentUserId = parseUserIdOrNull(authorization);
        return Result.ok(promptService.list(category, keyword, currentUserId));
    }

    @GetMapping("/detail/{id}")
    public Result<Prompt> detail(@PathVariable Long id,
                                 @RequestHeader("Authorization") String authorization) {
        Claims claims = parseClaims(authorization);
        return Result.ok(promptService.detail(id, ((Number) claims.get("userId")).longValue()));
    }

    @PostMapping("/add")
    public Result<Boolean> add(@RequestBody Prompt prompt,
                               @RequestHeader("Authorization") String authorization) {
        Claims claims = parseClaims(authorization);
        return Result.ok(promptService.add(
                prompt,
                ((Number) claims.get("userId")).longValue(),
                String.valueOf(claims.get("username"))
        ));
    }

    @PutMapping("/update")
    public Result<Boolean> update(@RequestBody Prompt prompt,
                                  @RequestHeader("Authorization") String authorization) {
        Claims claims = parseClaims(authorization);
        return Result.ok(promptService.update(prompt, ((Number) claims.get("userId")).longValue()));
    }

    @DeleteMapping("/delete/{id}")
    public Result<Boolean> delete(@PathVariable Long id,
                                  @RequestHeader("Authorization") String authorization) {
        Claims claims = parseClaims(authorization);
        return Result.ok(promptService.delete(id, ((Number) claims.get("userId")).longValue()));
    }

    @PutMapping("/toggle-private/{id}")
    public Result<Boolean> togglePrivate(@PathVariable Long id,
                                         @RequestParam Integer isPrivate,
                                         @RequestHeader("Authorization") String authorization) {
        Claims claims = parseClaims(authorization);
        return Result.ok(promptService.updatePrivate(id, isPrivate, ((Number) claims.get("userId")).longValue()));
    }

    @GetMapping("/mine")
    public Result<List<Prompt>> mine(@RequestHeader("Authorization") String authorization) {
        Claims claims = parseClaims(authorization);
        return Result.ok(promptService.mine(((Number) claims.get("userId")).longValue()));
    }

    private Claims parseClaims(String authorization) {
        String token = authorization.substring(7);
        return JwtUtils.parseToken(token);
    }

    private Long parseUserIdOrNull(String authorization) {
        try {
            if (authorization == null || !authorization.startsWith("Bearer ")) return null;
            Claims claims = parseClaims(authorization);
            return ((Number) claims.get("userId")).longValue();
        } catch (Exception e) {
            return null;
        }
    }
}
