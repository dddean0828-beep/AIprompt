package com.aiprompt.service;

import com.aiprompt.entity.User;

public interface UserService {
    User register(String username, String password);
    String login(String username, String password);
    User loginUser(String username, String password);
    User getById(Long userId);
}
