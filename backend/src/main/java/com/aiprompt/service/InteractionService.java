package com.aiprompt.service;

import com.aiprompt.entity.Favorite;
import com.aiprompt.entity.Prompt;
import com.aiprompt.dto.FavoritePromptVO;

import java.util.List;

public interface InteractionService {
    boolean addFavorite(Long userId, Long promptId);
    boolean removeFavorite(Long id);
    List<FavoritePromptVO> favoriteList(Long userId);
    boolean addUsage(Long userId, Long promptId);
    List<Favorite> rawFavoriteList(Long userId);
}
