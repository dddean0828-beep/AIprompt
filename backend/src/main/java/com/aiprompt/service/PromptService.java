package com.aiprompt.service;

import com.aiprompt.entity.Prompt;

import java.util.List;

public interface PromptService {
    List<Prompt> list(String category, String keyword, Long currentUserId);
    Prompt detail(Long id, Long currentUserId);
    boolean add(Prompt prompt, Long currentUserId, String currentUsername);
    boolean update(Prompt prompt, Long currentUserId);
    boolean delete(Long id, Long currentUserId);
    boolean updatePrivate(Long id, Integer isPrivate, Long currentUserId);
    List<Prompt> mine(Long currentUserId);
    List<Prompt> rankByHot();
    List<Prompt> rankByFavorite();
}
