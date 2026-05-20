package com.aiprompt.service.impl;

import com.aiprompt.dto.FavoritePromptVO;
import com.aiprompt.entity.Favorite;
import com.aiprompt.entity.Prompt;
import com.aiprompt.entity.UsageRecord;
import com.aiprompt.mapper.FavoriteMapper;
import com.aiprompt.mapper.PromptMapper;
import com.aiprompt.mapper.UsageRecordMapper;
import com.aiprompt.service.InteractionService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class InteractionServiceImpl implements InteractionService {
    private final FavoriteMapper favoriteMapper;
    private final UsageRecordMapper usageRecordMapper;
    private final PromptMapper promptMapper;

    @Override
    public boolean addFavorite(Long userId, Long promptId) {
        LambdaQueryWrapper<Favorite> wrapper = new LambdaQueryWrapper<Favorite>()
                .eq(Favorite::getUserId, userId)
                .eq(Favorite::getPromptId, promptId);
        Favorite exist = favoriteMapper.selectOne(wrapper);
        if (exist != null) {
            return true;
        }
        Favorite favorite = new Favorite();
        favorite.setUserId(userId);
        favorite.setPromptId(promptId);
        favorite.setCreatedAt(LocalDateTime.now());
        int inserted = favoriteMapper.insert(favorite);
        Prompt prompt = promptMapper.selectById(promptId);
        if (prompt != null) {
            prompt.setFavoriteCount((prompt.getFavoriteCount() == null ? 0 : prompt.getFavoriteCount()) + 1);
            promptMapper.updateById(prompt);
        }
        return inserted > 0;
    }

    @Override
    public boolean removeFavorite(Long id) {
        Favorite favorite = favoriteMapper.selectById(id);
        if (favorite != null) {
            Prompt prompt = promptMapper.selectById(favorite.getPromptId());
            if (prompt != null && prompt.getFavoriteCount() != null && prompt.getFavoriteCount() > 0) {
                prompt.setFavoriteCount(prompt.getFavoriteCount() - 1);
                promptMapper.updateById(prompt);
            }
        }
        return favoriteMapper.deleteById(id) > 0;
    }

    @Override
    public List<FavoritePromptVO> favoriteList(Long userId) {
        List<Favorite> favorites = rawFavoriteList(userId);
        List<FavoritePromptVO> result = new ArrayList<>();
        for (Favorite favorite : favorites) {
            Prompt prompt = promptMapper.selectById(favorite.getPromptId());
            if (prompt != null) {
                FavoritePromptVO vo = new FavoritePromptVO();
                vo.setFavoriteId(favorite.getId());
                vo.setPrompt(prompt);
                result.add(vo);
            }
        }
        return result;
    }

    @Override
    public boolean addUsage(Long userId, Long promptId) {
        UsageRecord usageRecord = new UsageRecord();
        usageRecord.setUserId(userId);
        usageRecord.setPromptId(promptId);
        usageRecord.setCreatedAt(LocalDateTime.now());
        int inserted = usageRecordMapper.insert(usageRecord);
        Prompt prompt = promptMapper.selectById(promptId);
        if (prompt != null) {
            prompt.setUseCount((prompt.getUseCount() == null ? 0 : prompt.getUseCount()) + 1);
            promptMapper.updateById(prompt);
        }
        return inserted > 0;
    }

    @Override
    public List<Favorite> rawFavoriteList(Long userId) {
        return favoriteMapper.selectList(new LambdaQueryWrapper<Favorite>()
                .eq(Favorite::getUserId, userId)
                .orderByDesc(Favorite::getCreatedAt));
    }
}
