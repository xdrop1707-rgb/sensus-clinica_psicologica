"use server";

import { createClient } from "@/lib/supabase/server";

export async function salvarProntuario(dados) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { error: "Você precisa estar logado." };
  }

  try {
    const { data: usuarioLogado } = await supabase
      .from("usuarios")
      .select("id")
      .eq("auth_user_id", user.id)
      .single();

    if (!usuarioLogado) {
      return { error: "Usuário não encontrado." };
    }

    const { data: psicologo } = await supabase
      .from("psicologos")
      .select("id")
      .eq("id_usuario", usuarioLogado.id)
      .single();

    if (!psicologo) {
      return { error: "Psicólogo não encontrado." };
    }

    const { data: consulta } = await supabase
      .from("consultas")
      .select("id_cliente")
      .eq("id", dados.id_consulta)
      .single();

    if (!consulta) {
      return { error: "Consulta não encontrada." };
    }

    const { data, error } = await supabase
      .from("prontuario")
      .insert({
        id_consulta: dados.id_consulta,
        id_psicologo: psicologo.id,
        id_cliente: consulta.id_cliente,
        data_anotacao: new Date().toISOString(),
        conteudo: dados.prontuario || "Sem anotações registradas nesta sessão.",
        status_clinico: dados.status_clinico || "Estável",
        humor_predominante: dados.humor_predominante || "Positivo",
        revisao_medicacao: dados.revisao_medicacao ?? false,
        intervencoes: dados.intervencoes || "Nenhuma",
        plano_proximo: dados.plano_proximo || "Continuar acompanhamento",
      })
      .select()
      .single();

    if (error) {
      return { error: "Erro ao salvar no Supabase: " + error.message };
    }

    return { success: true, prontuarioId: data.id };
  } catch (error) {
    return { error: "Erro inesperado: " + error.message };
  }
}

export async function enviarFeedback(dados) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { error: "Você precisa estar logado." };
  }

  try {
    // Busca o id do psicólogo logado
    const { data: usuarioLogado } = await supabase
      .from("usuarios")
      .select("id")
      .eq("auth_user_id", user.id)
      .single();

    if (!usuarioLogado) {
      return { error: "Usuário não encontrado." };
    }

    const { data: psicologo } = await supabase
      .from("psicologos")
      .select("id")
      .eq("id_usuario", usuarioLogado.id)
      .single();

    if (!psicologo) {
      return { error: "Psicólogo não encontrado." };
    }

    // Busca o id_cliente da consulta
    const { data: consulta } = await supabase
      .from("consultas")
      .select("id_cliente")
      .eq("id", dados.id_consulta)
      .single();

    if (!consulta) {
      return { error: "Consulta não encontrada." };
    }

    // Insere o feedback COM id_psicologo e id_cliente
    const { data, error } = await supabase
      .from("comunicacoes")
      .insert({
        id_consulta: dados.id_consulta,
        id_psicologo: psicologo.id, // <-- ADICIONADO
        id_cliente: consulta.id_cliente, // <-- ADICIONADO
        assunto: dados.assunto || "Orientação da Sessão",
        conteudo: dados.conteudo || "Sem conteúdo.",
        tipo: dados.tipo || "feedback",
        status: "enviado",
        data_envio: new Date().toISOString(),
      })
      .select()
      .single();

    if (error) {
      return { error: "Erro ao enviar feedback: " + error.message };
    }

    return { success: true, comunicacaoId: data.id };
  } catch (error) {
    return { error: "Erro inesperado: " + error.message };
  }
}
