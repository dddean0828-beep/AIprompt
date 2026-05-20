package com.aiprompt.service.impl;

import com.aiprompt.entity.Prompt;
import com.aiprompt.mapper.PromptMapper;
import com.aiprompt.service.PromptService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class PromptServiceImpl implements PromptService {
    private final PromptMapper promptMapper;

    @Override
    public List<Prompt> list(String category, String keyword, Long currentUserId) {
        LambdaQueryWrapper<Prompt> wrapper = new LambdaQueryWrapper<>();
        if (category != null && !category.isBlank()) {
            wrapper.eq(Prompt::getCategory, category);
        }
        if (keyword != null && !keyword.isBlank()) {
            wrapper.like(Prompt::getTitle, keyword);
        }
        if (currentUserId == null) {
            wrapper.eq(Prompt::getIsPrivate, 0);
        } else {
            wrapper.and(w -> w.eq(Prompt::getIsPrivate, 0).or().eq(Prompt::getCreatorId, currentUserId));
        }
        wrapper.orderByDesc(Prompt::getCreatedAt);
        return promptMapper.selectList(wrapper);
    }

    @Override
    public Prompt detail(Long id, Long currentUserId) {
        Prompt prompt = promptMapper.selectById(id);
        if (prompt == null) return null;
        if (Integer.valueOf(1).equals(prompt.getIsPrivate()) && !prompt.getCreatorId().equals(currentUserId)) {
            return null;
        }
        return prompt;
    }

    @Override
    public boolean add(Prompt prompt, Long currentUserId, String currentUsername) {
        prompt.setCreatedAt(LocalDateTime.now());
        prompt.setCreatorId(currentUserId);
        prompt.setCreatorName(currentUsername);
        if (prompt.getIsPrivate() == null) prompt.setIsPrivate(0);
        if (prompt.getUseCount() == null) prompt.setUseCount(0);
        if (prompt.getFavoriteCount() == null) prompt.setFavoriteCount(0);
        return promptMapper.insert(prompt) > 0;
    }

    @Override
    public boolean update(Prompt prompt, Long currentUserId) {
        Prompt dbPrompt = promptMapper.selectById(prompt.getId());
        if (dbPrompt == null || !dbPrompt.getCreatorId().equals(currentUserId)) return false;
        prompt.setCreatorId(dbPrompt.getCreatorId());
        prompt.setCreatorName(dbPrompt.getCreatorName());
        prompt.setCreatedAt(dbPrompt.getCreatedAt());
        return promptMapper.updateById(prompt) > 0;
    }

    @Override
    public boolean delete(Long id, Long currentUserId) {
        Prompt dbPrompt = promptMapper.selectById(id);
        if (dbPrompt == null || !dbPrompt.getCreatorId().equals(currentUserId)) return false;
        return promptMapper.deleteById(id) > 0;
    }

    @Override
    public boolean updatePrivate(Long id, Integer isPrivate, Long currentUserId) {
        Prompt dbPrompt = promptMapper.selectById(id);
        if (dbPrompt == null || !dbPrompt.getCreatorId().equals(currentUserId)) return false;
        dbPrompt.setIsPrivate(isPrivate == null ? 0 : (isPrivate == 0 ? 0 : 1));
        return promptMapper.updateById(dbPrompt) > 0;
    }

    @Override
    public List<Prompt> mine(Long currentUserId) {
        return promptMapper.selectList(new LambdaQueryWrapper<Prompt>()
                .eq(Prompt::getCreatorId, currentUserId)
                .orderByDesc(Prompt::getCreatedAt));
    }

    @Override
    public List<Prompt> rankByHot() {
        return promptMapper.selectList(new LambdaQueryWrapper<Prompt>().orderByDesc(Prompt::getUseCount));
    }

    @Override
    public List<Prompt> rankByFavorite() {
        return promptMapper.selectList(new LambdaQueryWrapper<Prompt>().orderByDesc(Prompt::getFavoriteCount));
    }
}
