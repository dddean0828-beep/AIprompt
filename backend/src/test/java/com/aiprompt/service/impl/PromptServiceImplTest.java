package com.aiprompt.service.impl;

import com.aiprompt.entity.Prompt;
import com.aiprompt.mapper.PromptMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentMatchers;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.io.Serializable;
import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PromptServiceImplTest {

    @Mock
    private PromptMapper promptMapper;

    @InjectMocks
    private PromptServiceImpl promptService;

    @Test
    @DisplayName("mine 应仅按 creatorId 查询")
    void mineDelegatesToMapper() {
        Long userId = 7L;
        Prompt p = new Prompt();
        p.setId(1L);
        p.setCreatorId(userId);
        when(promptMapper.selectList(ArgumentMatchers.any())).thenReturn(List.of(p));

        List<Prompt> result = promptService.mine(userId);

        assertThat(result).hasSize(1);
        assertThat(result.get(0).getCreatorId()).isEqualTo(userId);
        verify(promptMapper).selectList(ArgumentMatchers.any());
    }

    @Test
    @DisplayName("delete：非创建者不可删除")
    void deleteFailsWhenNotOwner() {
        Prompt db = new Prompt();
        db.setId(1L);
        db.setCreatorId(1L);
        when(promptMapper.selectById(1L)).thenReturn(db);

        boolean ok = promptService.delete(1L, 2L);

        assertThat(ok).isFalse();
        verify(promptMapper, never()).deleteById(ArgumentMatchers.<Serializable>any());
    }

    @Test
    @DisplayName("delete：创建者可删除")
    void deleteSucceedsWhenOwner() {
        Prompt db = new Prompt();
        db.setId(1L);
        db.setCreatorId(5L);
        when(promptMapper.selectById(1L)).thenReturn(db);
        when(promptMapper.deleteById(1L)).thenReturn(1);

        boolean ok = promptService.delete(1L, 5L);

        assertThat(ok).isTrue();
        verify(promptMapper).deleteById(1L);
    }

    @Test
    @DisplayName("detail：私密且非创建者应返回 null")
    void detailPrivateNotVisibleToOthers() {
        Prompt db = new Prompt();
        db.setId(1L);
        db.setIsPrivate(1);
        db.setCreatorId(1L);
        when(promptMapper.selectById(1L)).thenReturn(db);

        Prompt out = promptService.detail(1L, 2L);

        assertThat(out).isNull();
    }

    @Test
    @DisplayName("detail：私密但创建者本人可查看")
    void detailPrivateVisibleToOwner() {
        Prompt db = new Prompt();
        db.setId(1L);
        db.setIsPrivate(1);
        db.setCreatorId(3L);
        when(promptMapper.selectById(1L)).thenReturn(db);

        Prompt out = promptService.detail(1L, 3L);

        assertThat(out).isNotNull();
        assertThat(out.getId()).isEqualTo(1L);
    }

    @Test
    @DisplayName("list：调用 mapper.selectList 并返回结果")
    void listDelegatesToMapper() {
        when(promptMapper.selectList(ArgumentMatchers.any())).thenReturn(Collections.emptyList());

        List<Prompt> result = promptService.list(null, null, 10L);

        assertThat(result).isEmpty();
        verify(promptMapper).selectList(ArgumentMatchers.any());
    }
}
