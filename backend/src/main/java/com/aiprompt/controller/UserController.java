package com.aiprompt.controller;

import com.aiprompt.common.Result;
import com.aiprompt.dto.AuthRequest;
import com.aiprompt.entity.User;
import com.aiprompt.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @PostMapping("/register")
    public Result<User> register(@RequestBody AuthRequest request) {
        User user = userService.register(request.getUsername(), request.getPassword());
        if (user == null) {
            return Result.fail("用户名已存在");
        }
        return Result.ok("注册成功", user);
    }

    @PostMapping("/login")
    public Result<Map<String, String>> login(@RequestBody AuthRequest request) {
        String token = userService.login(request.getUsername(), request.getPassword());
        User user = userService.loginUser(request.getUsername(), request.getPassword());
        if (token == null) {
            return Result.fail("用户名或密码错误");
        }
        Map<String, String> map = new HashMap<>();
        map.put("token", token);
        map.put("userId", String.valueOf(user.getId()));
        return Result.ok("登录成功", map);
    }

    @GetMapping("/info")
    public Result<User> info(@RequestParam Long userId) {
        return Result.ok(userService.getById(userId));
    }
}
