package com.aiprompt.service.impl;

import com.aiprompt.entity.User;
import com.aiprompt.mapper.UserMapper;
import com.aiprompt.service.UserService;
import com.aiprompt.utils.JwtUtils;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {
    private final UserMapper userMapper;

    @Override
    public User register(String username, String password) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<User>()
                .eq(User::getUsername, username);
        User exist = userMapper.selectOne(wrapper);
        if (exist != null) {
            return null;
        }
        User user = new User();
        user.setUsername(username);
        user.setPassword(password);
        user.setCreatedAt(LocalDateTime.now());
        userMapper.insert(user);
        return user;
    }

    @Override
    public String login(String username, String password) {
        User user = loginUser(username, password);
        return user == null ? null : JwtUtils.createToken(user.getId(), user.getUsername());
    }

    @Override
    public User loginUser(String username, String password) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<User>()
                .eq(User::getUsername, username)
                .eq(User::getPassword, password);
        return userMapper.selectOne(wrapper);
    }

    @Override
    public User getById(Long userId) {
        return userMapper.selectById(userId);
    }
}
