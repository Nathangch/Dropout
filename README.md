<div align="center">
  <img src="assets/backgrounds/menu_bg.jpg" alt="Dropout Banner" width="100%">
  
  <h1>🐐 DROPOUT</h1>
  <p><strong>A maldição musical. O silêncio absoluto. Uma corrida desenfreada pela sobrevivência.</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Engine-PyGame-%23EE4C2C?style=for-the-badge&logo=python&logoColor=white" alt="PyGame">
    <img src="https://img.shields.io/badge/Language-Python-%233776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Status-Beta-%23FFB000?style=for-the-badge" alt="Status">
  </p>
</div>

## 📜 Sobre o Jogo

**Dropout** é um *Endless Runner* atmosférico desenvolvido em Python puro (PyGame). Você guia **Japeth**, um pequeno bode carismático que foi alvo de uma praga terrível: ele é forçado a cantar absolutamente tudo o que pensa ou fala de forma constrangedora.

Em busca do lendário **Berrante Silencioso**, Japeth precisará cruzar florestas perigosas, desertos escaldantes e o impiedoso topo das montanhas nevadas para, enfim, conquistar a paz de uma mente quieta.

## ✨ Características Principais

- 🏔️ **Terreno Orgânico Procedural:** O ambiente não é reto! Desníveis orgânicos, penhascos e vales são gerados dinamicamente baseados em lógica matemática de Múltiplos Senos Harmônicos (Multi-Octave Noise), garantindo montanhas imprevisíveis que nunca se repetem sozinhas.
- 💨 **Movimentação Viva (Momentum):** Sistema dinâmico físico de Momentum gravitacional. Você ganha velocidade ao correr em descidas e perde velocidade atritando contra as subidas íngremes.
- 🦅 **Física de Voo e Dash:** Segure `ESPAÇO` para abrir sua asa-delta (Planar) gastando sua estamina duramente conquistada no ar, ou quebre a barreira do vento gastando um pedaço fixo da barra num impulso lateral rápido usando o `SHIFT`.
- ⛅ **Clima Parallax Constante:** Mais de 5 camadas independentes de ilusão de profundidade compõem o horizonte com um complexo sistema de partículas independentes (Folhas, Poeira e Nevascas).
- 🦇 **Hitboxes Inteligentes:** Caixas de colisão de monstros suavizadas em 40% nas margens perimetrais ("Fairness Logic") penalizando apenas erros reais sem ferir o jogador injustamente por pixels estéticos!

<div align="center">
  <img src="assets/sprites/idle.png" width="300">
</div>

---

## 🎮 Como Jogar

| Ação | Tecla Principal | Tecla Secundária |
|---|---|---|
| **Pular** | `ESPAÇO` | `SETA PRA CIMA` / `W` |
| **Pulo Duplo** | `ESPAÇO` (No ar) | `SETA P/ CIMA` (No ar) |
| **Planar** | `Segurar ESPAÇO` (No ar)| --- |
| **Dash (Impulso)** | `SHIFT` | --- |
| **Pausar Menu** | `ESC` | --- |

*(Nota: O uso das habilidades especiais como o Dash e a Planagem é compartilhado através da barra cinza e amarela de vitalidade (Estamina/Momentum) no topo esquerdo da tela! Saiba gerenciar a energia.)*

---

## 🚀 Instalação e Uso

1. Clone este repositório ou faça o download em `.ZIP`.
2. Certifique-se de que possui o **Python 3.10+** (ou superior) já instalado na sua máquina.
3. Instale a biblioteca base do motor gráfico rodando no seu terminal:
   ```bash
   pip install pygame
   ```
4. Execute o jogo iniciando o pacote mestre:
   ```bash
   python main.py
   ```

---

## 🛠️ Arquitetura do Software

O Dropout não é feito numa Engine fechada, foi construído em arquitetura raiz (`Pygame`) com extremo rigor a padronizações profissionais de Software Engineering:
*   **Decoupled Entities**: Separação clara entre Renderização de Partículas, Mecânicas do Player, UI Automática Animada (LERP) e Sistemas de Bioma/Atrito.
*   **Factory Pattern**: Todos os monstros são gerados de forma modular baseada numa fábrica autônoma que decide escalar sprites e recriar instâncias sem sujar o código do loop principal.
*   **Object Pooling**: Tempestades de partículas são salvas e reutilizadas da memória RAM da sua máquina descartando "Garbage Collectors" do Python que causam travadas/engasgos (stutters).

<div align="center">
  <p>Feito com ❤️ por mentes curiosas, perseverança e dezenas de linhas de código.</p>
</div>
