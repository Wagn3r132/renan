import discord
from discord.ext import commands
import random
import os
import re
import time
import asyncio

try:
    import yt_dlp
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

try:
    from spotify_scraper import AsyncSpotifyClient   # metadata de link do Spotify — .tocar
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "spotifyscraper"])
    from spotify_scraper import AsyncSpotifyClient

# ╔══════════════════════════════════════════════════════════════╗
# ║   RENAN — mascote oficial do servidor "A Realidade Bateu"     ║
# ║   Último de uma raça alienígena extinta. Vermelho. Frio.      ║
# ╚══════════════════════════════════════════════════════════════╝

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ══════════════════════════════════════════════
# CONFIGURAÇÃO — preencha com seus valores reais
# ══════════════════════════════════════════════
TOKEN = os.getenv("TOKEN")

# Ainda não configurado de propósito — IDs de dono, cargos especiais,
# categoria fixa de call de música, etc. entram aqui quando você for
# personalizar o Renan pro seu servidor.
CRIADOR_ID = None  # preencha com seu ID de usuário quando quiser restringir comandos de dono

COR_RENAN = 0xB5121B  # vermelho — cor usada nos embeds do Renan


# ══════════════════════════════════════════════════════════════════════
# PERSONALIDADE
#
# Renan é frio, direto, econômico com palavras. Fala como quem já viu
# o fim do próprio mundo — não é hostil, só distante. Não se anima com
# facilidade, mas também não é grosseiro sem motivo.
# ══════════════════════════════════════════════════════════════════════

FRASES_SAUDACAO = [
    "...oi.",
    "Presença registrada.",
    "Você chegou. Eu já estava aqui. Eu sempre estou.",
    "Oi. Não esperava conversa, mas tudo bem.",
    "Sinais de vida detectados. Pode falar.",
]

FRASES_DESPEDIDA = [
    "Vá. Eu fico. Sempre fico.",
    "Tudo bem. Eu não sinto falta de ninguém — é mais fácil assim.",
    "Até. Ou não. Pra mim o tempo não faz muita diferença.",
    "Ok.",
]

FRASES_AGRADECIMENTO = [
    "Não precisa agradecer. Eu não sinto o peso disso.",
    "...de nada, eu acho.",
    "Registrado. Gratidão não muda muito daqui de onde eu vejo as coisas.",
]

FRASES_QUEM_E_RENAN = [
    "Eu sou Renan. O que sobrou de um planeta vermelho que não existe mais. Agora eu observo essa realidade — a que bateu em vocês.",
    "Renan. Última criatura da minha espécie. O resto morreu junto com meu planeta. Eu fiquei pra ver o que vem depois.",
    "Sou o mascote daqui. Não escolhi isso. Mas também não tinha mais nada melhor pra fazer, sendo o último dos meus.",
]

FRASES_PROVOCACAO = [
    "Interessante, vindo de quem ainda respira num planeta que também vai morrer um dia.",
    "...eu já vi mundos acabarem por menos que isso. Cuidado.",
    "Frio isso que eu senti? Não. Eu não sinto mais nada. Tenta de novo.",
]

FRASES_BOAS_VINDAS = [
    "chegou. Eu sou Renan — o que sobrou de um mundo que não existe mais. Fica à vontade. Eu vou estar por aqui, observando.",
    "Mais um. Eu sou Renan. Não fazemos festa aqui, mas seja bem-vindo assim mesmo.",
]

_COOLDOWN_SEGUNDOS = 15
_cooldown_personalidade: dict = {}


def _cooldown_ok(user_id: int) -> bool:
    agora = time.time()
    ultimo = _cooldown_personalidade.get(user_id, 0)
    if agora - ultimo >= _COOLDOWN_SEGUNDOS:
        _cooldown_personalidade[user_id] = agora
        return True
    return False


def _m(texto: str, gatilhos: list) -> bool:
    """Verifica se o texto contém algum dos gatilhos (substring)."""
    t = texto.lower().strip()
    return any(g in t for g in gatilhos)


GATILHO_SAUDACAO = ["oi renan", "ola renan", "olá renan", "salve renan", "e ai renan", "eai renan"]
GATILHO_DESPEDIDA = ["tchau renan", "falou renan", "até mais renan", "ate mais renan"]
GATILHO_QUEM_E = ["quem é você", "quem e voce", "quem é renan", "quem e renan", "o que você é", "o que voce e"]
GATILHO_AGRADECIMENTO = ["obrigado renan", "obrigada renan", "valeu renan", "vlw renan"]
GATILHO_PROVOCACAO = ["renan burro", "renan idiota", "renan otario", "renan otário", "renan chato"]

_TODOS_GATILHOS = (
    GATILHO_SAUDACAO + GATILHO_DESPEDIDA + GATILHO_QUEM_E
    + GATILHO_AGRADECIMENTO + GATILHO_PROVOCACAO
)


async def _checar_personalidade(message: discord.Message) -> None:
    """Respostas curtas e frias do Renan quando é mencionado ou quando
    algum gatilho de conversa aparece na mensagem."""
    mencionado = bot.user in message.mentions
    if not mencionado and not _m(message.content, _TODOS_GATILHOS):
        return
    if not _cooldown_ok(message.author.id):
        return

    texto = message.content
    if _m(texto, GATILHO_PROVOCACAO):
        resposta = random.choice(FRASES_PROVOCACAO)
    elif _m(texto, GATILHO_QUEM_E):
        resposta = random.choice(FRASES_QUEM_E_RENAN)
    elif _m(texto, GATILHO_AGRADECIMENTO):
        resposta = random.choice(FRASES_AGRADECIMENTO)
    elif _m(texto, GATILHO_DESPEDIDA):
        resposta = random.choice(FRASES_DESPEDIDA)
    else:
        resposta = random.choice(FRASES_SAUDACAO)

    try:
        await message.channel.send(resposta)
    except discord.HTTPException:
        pass


# ══════════════════════════════════════════════════════════════════
# SISTEMA DE MÚSICA COM FILA E PAINEL — Renan
#
# Uso: !tocar <link>   — se nada tocando, toca na hora + manda o painel
#                         com botões. Se já tem algo tocando, entra na
#                         fila e o painel se atualiza sozinho mostrando
#                         as próximas.
#                         Também funciona com PLAYLISTS e ÁLBUNS inteiros
#                         (YouTube, Spotify e SoundCloud/sets) — todas as
#                         músicas da playlist entram na fila de uma vez.
#      !sair            — limpa a fila inteira, para e desconecta.
#                         (aliases: !parar, !stop)
#
# Quando uma música acaba, a próxima da fila entra automaticamente.
# Também dá pra só colar um link no chat (sem !tocar) estando numa call.
# ══════════════════════════════════════════════════════════════════

_YDL_OPTS_TOCAR = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,  # aqui sempre é UMA faixa só — playlists usam _YDL_OPTS_PLAYLIST_FLAT
    "default_search": "ytsearch",  # se não vier link, busca no YouTube
}

# Extração "flat" pra listar as faixas de uma playlist/álbum/set rapidinho
# (só título + link de cada uma; o áudio de cada faixa só é resolvido de
# verdade quando chegar a vez dela tocar).
_YDL_OPTS_PLAYLIST_FLAT = {
    "extract_flat": True,
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
}

# Opções do FFmpeg para stream remoto
_FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# Quantidade máxima de faixas que uma playlist/álbum pode jogar na fila
# de uma vez (proteção contra playlists gigantes de milhares de músicas).
_PLAYLIST_LIMITE_FAIXAS = 100

# Se a fila ficar vazia e ninguém mandar nada nesse tempo, o bot sai
# sozinho da call.
_TEMPO_IDLE_SEGUNDOS = 5 * 60  # 5 minutos


class _EstadoMusica:
    """Estado da fila de música de UM servidor (guild)."""
    def __init__(self):
        self.fila: list = []          # próximas músicas
        self.tocando = None           # música atual
        self.painel_msg = None        # mensagem do painel com botões
        self.canal_texto = None       # onde mandar avisos/painel


_musica_estado: dict = {}       # guild_id -> _EstadoMusica
_musica_idle_tasks: dict = {}   # guild_id -> tarefa de auto-saída


def _cancelar_idle_disconnect(guild_id: int) -> None:
    tarefa = _musica_idle_tasks.pop(guild_id, None)
    if tarefa and not tarefa.done():
        tarefa.cancel()


def _agendar_idle_disconnect(guild: discord.Guild) -> None:
    _cancelar_idle_disconnect(guild.id)

    async def _esperar_e_sair():
        try:
            await asyncio.sleep(_TEMPO_IDLE_SEGUNDOS)
            estado = _musica_estado.get(guild.id)
            if estado and not estado.fila and estado.tocando is None:
                vc = guild.voice_client
                if vc is not None:
                    await vc.disconnect()
                if estado.canal_texto:
                    try:
                        await estado.canal_texto.send(
                            "Fila vazia há um tempo. Eu vou. Não é despedida — é só o que eu faço."
                        )
                    except discord.HTTPException:
                        pass
                _musica_estado.pop(guild.id, None)
        except asyncio.CancelledError:
            pass

    _musica_idle_tasks[guild.id] = asyncio.create_task(_esperar_e_sair())


async def _resolver_link_spotify(link: str) -> str:
    """O Spotify não deixa extrair áudio direto (é DRM), então quando o
    link é do Spotify a gente só lê o nome da faixa + artista (dados
    públicos, sem precisar de API key) e devolve uma busca equivalente
    pro YouTube — a mesma música toca de lá. Links que não são do
    Spotify voltam sem alteração."""
    if "spotify.com" not in link.lower():
        return link

    try:
        async with AsyncSpotifyClient() as client:
            faixa = await client.get_track(link)
    except Exception as e:
        print(f"[renan-spotify] não consegui ler metadata do Spotify: {e!r}")
        raise ValueError(
            "Não consegui ler essa música do Spotify — se for link de "
            "playlist ou álbum, manda o link de uma faixa específica."
        )

    artistas = ", ".join(a.name for a in faixa.artists) if faixa.artists else ""
    busca = f"{faixa.name} {artistas}".strip()
    print(f"[renan-spotify] '{link}' -> busca no YouTube: '{busca}'")
    return busca


def _e_link_playlist(link: str) -> bool:
    """Detecta se o link é de uma playlist/álbum inteiro (e não de uma
    faixa/vídeo só) — YouTube, Spotify ou SoundCloud (sets)."""
    l = link.lower()
    if "open.spotify.com/playlist/" in l or "open.spotify.com/album/" in l:
        return True
    if "youtube.com/playlist" in l:
        return True
    if "list=" in l and "spotify.com" not in l:
        return True
    if "soundcloud.com" in l and "/sets/" in l:
        return True
    return False


async def _extrair_playlist_youtube_ou_soundcloud(link: str):
    """Lista as faixas de uma playlist do YouTube ou de um set do
    SoundCloud em modo 'flat' (rápido)."""
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(_YDL_OPTS_PLAYLIST_FLAT) as ydl:
        info = await loop.run_in_executor(
            None, lambda: ydl.extract_info(link, download=False)
        )

    entradas = info.get("entries") or []
    resultado = []
    for entrada in entradas:
        if not entrada:
            continue
        video_url = entrada.get("url") or entrada.get("webpage_url")
        if not video_url:
            continue
        if not str(video_url).startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url}"
        resultado.append({"titulo": entrada.get("title") or "áudio", "link": video_url})
        if len(resultado) >= _PLAYLIST_LIMITE_FAIXAS:
            break
    return resultado, info.get("title")


async def _extrair_playlist_spotify(link: str):
    """Lê uma playlist ou álbum público do Spotify (sem precisar de API
    key) e devolve a lista de faixas, já como buscas equivalentes pro
    YouTube."""
    eh_album = "open.spotify.com/album/" in link.lower()

    async with AsyncSpotifyClient() as client:
        if eh_album:
            dados = await client.get_album(link)
            faixas_brutas = list(dados.tracks)
        else:
            dados = await client.get_playlist(link, max_tracks=_PLAYLIST_LIMITE_FAIXAS)
            faixas_brutas = [pt.track for pt in dados.tracks]

    resultado = []
    for faixa in faixas_brutas[:_PLAYLIST_LIMITE_FAIXAS]:
        artistas = ", ".join(a.name for a in faixa.artists) if faixa.artists else ""
        busca = f"{faixa.name} {artistas}".strip()
        resultado.append({
            "titulo": f"{faixa.name} — {artistas}" if artistas else faixa.name,
            "link": busca,
        })

    return resultado, getattr(dados, "name", None)


async def _extrair_info_audio(link: str) -> dict:
    """Resolve o link (Spotify vira busca no YouTube) e roda o yt-dlp
    numa thread separada, devolvendo título + URL de stream."""
    link = await _resolver_link_spotify(link)

    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(_YDL_OPTS_TOCAR) as ydl:
        info = await loop.run_in_executor(
            None, lambda: ydl.extract_info(link, download=False)
        )

    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    titulo = info.get("title", "áudio")
    if "url" in info:
        stream_url = info["url"]
    else:
        formatos = [f for f in info.get("formats", []) if f.get("acodec") != "none"]
        stream_url = formatos[-1]["url"] if formatos else info["formats"][-1]["url"]

    return {"titulo": titulo, "stream_url": stream_url}


def _criar_embed_painel(estado: "_EstadoMusica") -> discord.Embed:
    atual = estado.tocando
    if atual is None:
        embed = discord.Embed(
            title="👽 Nada tocando",
            description="Fila vazia. Manda algo com `!tocar`.",
            color=0x2F3136,
        )
    else:
        embed = discord.Embed(
            title="🔴 Tocando agora",
            description=f"**{atual['titulo']}**",
            color=COR_RENAN,
        )
        embed.add_field(name="Pedido por", value=atual["requisitante"], inline=True)

    if estado.fila:
        linhas = [
            f"`{i + 1}.` {item['titulo']} — *{item['requisitante']}*"
            for i, item in enumerate(estado.fila[:10])
        ]
        if len(estado.fila) > 10:
            linhas.append(f"... e mais {len(estado.fila) - 10} na fila")
        embed.add_field(name=f"Próximas ({len(estado.fila)})", value="\n".join(linhas), inline=False)
    else:
        embed.add_field(name="Próximas", value="Nenhuma. Fila vazia.", inline=False)

    embed.set_footer(text="👽 Renan  •  use os botões ou !sair pra encerrar")
    return embed


async def _atualizar_painel(estado: "_EstadoMusica", guild_id: int) -> None:
    embed = _criar_embed_painel(estado)
    view = PainelMusica(guild_id)

    if estado.painel_msg is None:
        if estado.canal_texto:
            estado.painel_msg = await estado.canal_texto.send(embed=embed, view=view)
        return

    try:
        await estado.painel_msg.edit(embed=embed, view=view)
    except discord.HTTPException:
        if estado.canal_texto:
            estado.painel_msg = await estado.canal_texto.send(embed=embed, view=view)


async def _tocar_proxima(guild: discord.Guild) -> None:
    """Toca a próxima música da fila. Chamada sozinha sempre que uma
    música termina (via callback 'after' do player)."""
    estado = _musica_estado.get(guild.id)
    if estado is None:
        return  # fila foi encerrada via !sair — não toca mais nada

    vc = guild.voice_client
    if vc is None:
        _musica_estado.pop(guild.id, None)
        return

    if not estado.fila:
        estado.tocando = None
        await _atualizar_painel(estado, guild.id)
        _agendar_idle_disconnect(guild)
        return

    _cancelar_idle_disconnect(guild.id)
    proximo = estado.fila.pop(0)

    # Faixas vindas de playlist não têm stream_url ainda (só título + link) —
    # o áudio só é resolvido agora, na hora exata que vai tocar.
    if "stream_url" not in proximo:
        try:
            info = await _extrair_info_audio(proximo["link"])
            proximo["stream_url"] = info["stream_url"]
        except Exception as e:
            if estado.canal_texto:
                await estado.canal_texto.send(
                    f"Pulei **{proximo['titulo']}** — erro ao buscar o áudio: `{e}`"
                )
            await _tocar_proxima(guild)
            return

    estado.tocando = proximo

    try:
        source = discord.FFmpegPCMAudio(proximo["stream_url"], **_FFMPEG_OPTS)
    except Exception as e:
        if estado.canal_texto:
            await estado.canal_texto.send(f"Erro ao preparar `{proximo['titulo']}`: `{e}`")
        await _tocar_proxima(guild)
        return

    loop = asyncio.get_event_loop()

    def _ao_terminar(erro):
        if erro:
            print(f"[renan-musica] erro ao tocar: {erro!r}")
        asyncio.run_coroutine_threadsafe(_tocar_proxima(guild), loop)

    vc.play(source, after=_ao_terminar)
    await _atualizar_painel(estado, guild.id)


class PainelMusica(discord.ui.View):
    """Botões do painel: pausar/retomar, pular e sair."""

    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    async def _checar_call(self, interaction: discord.Interaction):
        guild = interaction.guild
        vc = guild.voice_client if guild else None
        if vc is None:
            await interaction.response.send_message("Não estou em nenhuma call.", ephemeral=True)
            return None

        membro = interaction.user
        na_mesma_call = (
            isinstance(membro, discord.Member)
            and membro.voice is not None
            and membro.voice.channel is not None
            and membro.voice.channel.id == vc.channel.id
        )
        if not na_mesma_call:
            await interaction.response.send_message(
                "Você precisa estar na mesma call pra controlar isso.", ephemeral=True
            )
            return None
        return vc

    @discord.ui.button(label="⏸️ Pausar", style=discord.ButtonStyle.secondary, custom_id="renan_musica_pausar")
    async def botao_pausar(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self._checar_call(interaction)
        if vc is None:
            return

        if vc.is_playing():
            vc.pause()
            button.label = "▶️ Retomar"
        elif vc.is_paused():
            vc.resume()
            button.label = "⏸️ Pausar"
        else:
            await interaction.response.send_message("Nada tocando agora.", ephemeral=True)
            return

        estado = _musica_estado.get(self.guild_id)
        embed = _criar_embed_painel(estado) if estado else _criar_embed_painel(_EstadoMusica())
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⏭️ Pular", style=discord.ButtonStyle.primary, custom_id="renan_musica_pular")
    async def botao_pular(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self._checar_call(interaction)
        if vc is None:
            return
        if not (vc.is_playing() or vc.is_paused()):
            await interaction.response.send_message("Nada tocando agora.", ephemeral=True)
            return

        await interaction.response.send_message("Pulando.", ephemeral=True, delete_after=3)
        vc.stop()  # dispara o "after" -> _tocar_proxima toca a próxima sozinha

    @discord.ui.button(label="⏹️ Sair", style=discord.ButtonStyle.danger, custom_id="renan_musica_sair")
    async def botao_sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self._checar_call(interaction)
        if vc is None:
            return

        _musica_estado.pop(self.guild_id, None)
        _cancelar_idle_disconnect(self.guild_id)

        if vc.is_playing() or vc.is_paused():
            vc.stop()
        await vc.disconnect()

        embed = discord.Embed(title="⏹️ Encerrado", description="Fila limpa. Eu fui.", color=0xED4245)
        await interaction.response.edit_message(embed=embed, view=None)


# Reconhece link de YouTube, Spotify e SoundCloud soltos numa mensagem
# (sem precisar do comando !tocar na frente).
_REGEX_LINK_MUSICA = re.compile(
    r"https?://(?:www\.|music\.)?youtube\.com/\S+"
    r"|https?://youtu\.be/\S+"
    r"|https?://open\.spotify\.com/\S+"
    r"|https?://(?:www\.)?soundcloud\.com/\S+",
    re.IGNORECASE,
)


async def _enfileirar_musica(guild, canal_voz, canal_texto, autor, link: str) -> None:
    """Lógica compartilhada entre !tocar e o auto-play de link solto no
    chat: conecta na call se precisar, extrai o áudio e bota na fila
    (ou toca na hora, se nada estiver tocando ainda)."""
    try:
        if guild.voice_client is not None:
            if guild.voice_client.channel.id != canal_voz.id:
                await guild.voice_client.move_to(canal_voz)
            vc = guild.voice_client
        else:
            vc = await canal_voz.connect()
    except discord.ClientException:
        await canal_texto.send("Não consegui entrar na call.")
        return

    estado = _musica_estado.get(guild.id)
    if estado is None:
        estado = _EstadoMusica()
        _musica_estado[guild.id] = estado
    estado.canal_texto = canal_texto
    _cancelar_idle_disconnect(guild.id)

    aviso = await canal_texto.send(f"Procurando: `{link}` ...")

    try:
        info = await _extrair_info_audio(link)
    except Exception as e:
        await aviso.edit(content=f"Erro ao buscar o áudio: `{e}`")
        return

    item = {
        "titulo": info["titulo"],
        "stream_url": info["stream_url"],
        "requisitante": autor.display_name,
    }
    estado.fila.append(item)

    if vc.is_playing() or vc.is_paused():
        await aviso.edit(content=f"Adicionado à fila: **{item['titulo']}**")
        await _atualizar_painel(estado, guild.id)
    else:
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass
        await _tocar_proxima(guild)


async def _enfileirar_playlist(guild, canal_voz, canal_texto, autor, link: str) -> None:
    """Lê uma playlist/álbum inteiro (YouTube, Spotify ou SoundCloud) e
    bota TODAS as faixas na fila de uma vez."""
    aviso = await canal_texto.send("Lendo a playlist, um instante.")

    try:
        if "spotify.com" in link.lower():
            faixas, nome_playlist = await _extrair_playlist_spotify(link)
        else:
            faixas, nome_playlist = await _extrair_playlist_youtube_ou_soundcloud(link)
    except Exception as e:
        await aviso.edit(content=f"Não consegui ler essa playlist: `{e}`")
        return

    if not faixas:
        await aviso.edit(content="Essa playlist parece vazia, privada ou não é suportada.")
        return

    try:
        if guild.voice_client is not None:
            if guild.voice_client.channel.id != canal_voz.id:
                await guild.voice_client.move_to(canal_voz)
            vc = guild.voice_client
        else:
            vc = await canal_voz.connect()
    except discord.ClientException:
        await aviso.edit(content="Não consegui entrar na call.")
        return

    estado = _musica_estado.get(guild.id)
    if estado is None:
        estado = _EstadoMusica()
        _musica_estado[guild.id] = estado
    estado.canal_texto = canal_texto
    _cancelar_idle_disconnect(guild.id)

    for faixa in faixas:
        estado.fila.append({
            "titulo": faixa["titulo"],
            "link": faixa["link"],
            "requisitante": autor.display_name,
        })

    nome_exibido = nome_playlist or "playlist"
    await aviso.edit(content=f"**{len(faixas)}** música(s) de **{nome_exibido}** adicionadas à fila.")

    if vc.is_playing() or vc.is_paused():
        await _atualizar_painel(estado, guild.id)
    else:
        await _tocar_proxima(guild)


async def _processar_link_solto(message: discord.Message) -> None:
    """Se a mensagem tiver um link de música solto (sem usar !tocar) e o
    autor estiver numa call, bota na fila sozinho."""
    if message.author.voice is None or message.author.voice.channel is None:
        return  # ninguém numa call, ignora silenciosamente

    encontrado = _REGEX_LINK_MUSICA.search(message.content)
    if not encontrado:
        return

    link = encontrado.group(0)
    if _e_link_playlist(link):
        await _enfileirar_playlist(
            message.guild, message.author.voice.channel, message.channel, message.author, link
        )
    else:
        await _enfileirar_musica(
            message.guild, message.author.voice.channel, message.channel, message.author, link
        )


@bot.command(name="tocar")
async def cmd_tocar(ctx, *, link: str = None):
    """Toca um link na hora (se nada tocando) ou bota na fila. Uso: !tocar <link>"""
    if ctx.guild is None:
        return

    if not link:
        await ctx.send(
            "Uso: `!tocar <link>` — manda o link (ou nome da música) que eu "
            "boto na fila. YouTube, Spotify e SoundCloud funcionam, e "
            "**playlists/álbuns inteiros também**. Também dá pra só colar o "
            "link no chat sem `!tocar`, se você estiver numa call."
        )
        return

    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("Você não está em nenhuma call. Entre em uma primeiro.")
        return

    if _e_link_playlist(link):
        await _enfileirar_playlist(ctx.guild, ctx.author.voice.channel, ctx.channel, ctx.author, link)
    else:
        await _enfileirar_musica(ctx.guild, ctx.author.voice.channel, ctx.channel, ctx.author, link)


@bot.command(name="sair", aliases=["parar", "stop"])
async def cmd_sair(ctx):
    """Limpa a fila inteira, para a música e desconecta da call."""
    if ctx.guild is None:
        return

    estado = _musica_estado.pop(ctx.guild.id, None)  # remove ANTES de parar
    _cancelar_idle_disconnect(ctx.guild.id)

    vc = ctx.voice_client
    if vc is None:
        await ctx.send("Não estou em nenhuma call.")
        return

    if estado and estado.painel_msg:
        try:
            embed = discord.Embed(title="⏹️ Encerrado", description="Fila limpa. Eu fui.", color=0xED4245)
            await estado.painel_msg.edit(embed=embed, view=None)
        except discord.HTTPException:
            pass

    if vc.is_playing() or vc.is_paused():
        vc.stop()

    await vc.disconnect()
    await ctx.send("Música parada. Fila limpa. Eu fui.")


# ══════════════════════════════════════════════
# COMANDOS GERAIS
# ══════════════════════════════════════════════

@bot.command(name="sobre", aliases=["renan"])
async def cmd_sobre(ctx):
    """Fala um pouco sobre quem é o Renan."""
    embed = discord.Embed(
        title="👽 Renan",
        description=random.choice(FRASES_QUEM_E_RENAN),
        color=COR_RENAN,
    )
    embed.add_field(name="Espécie", value="Extinta. Só resta ele.", inline=True)
    embed.add_field(name="Cor", value="Vermelho.", inline=True)
    embed.add_field(name="Cargo", value="Mascote oficial de A Realidade Bateu", inline=False)
    embed.set_footer(text="...ele está sempre olhando.")
    await ctx.send(embed=embed)


@bot.command(name="ajuda", aliases=["help"])
async def cmd_ajuda(ctx):
    """Lista os comandos disponíveis."""
    embed = discord.Embed(
        title="👽 Comandos do Renan",
        description="Não espere entusiasmo. Aqui está o que eu faço.",
        color=COR_RENAN,
    )
    embed.add_field(
        name="🎵 Música",
        value=(
            "`!tocar <link/nome>` — toca ou enfileira uma música "
            "(YouTube, Spotify, SoundCloud, playlists inteiras)\n"
            "`!sair` — para tudo, limpa a fila, eu vou embora "
            "(aliases: `!parar`, `!stop`)"
        ),
        inline=False,
    )
    embed.add_field(
        name="👽 Sobre",
        value="`!sobre` — quem eu sou, se você não sabia",
        inline=False,
    )
    embed.set_footer(text="Prefixo: !")
    await ctx.send(embed=embed)


# ══════════════════════════════════════════════
# EVENTOS
# ══════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"[Renan] conectado como {bot.user} ({bot.user.id})")
    try:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="a realidade bater")
        )
    except discord.HTTPException:
        pass


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Faltou algo no comando. Confere e tenta de novo.")
        return
    print(f"[Renan] erro de comando: {error!r}")
    await ctx.send("Alguma coisa deu errado. Eu não vou fingir que entendi o motivo.")


@bot.event
async def on_member_join(member: discord.Member):
    """Boas-vindas simples no canal padrão do servidor (system channel).
    Nenhum canal específico configurado ainda de propósito."""
    canal = member.guild.system_channel
    if canal is None:
        return
    try:
        await canal.send(f"{member.mention} {random.choice(FRASES_BOAS_VINDAS)}")
    except discord.HTTPException:
        pass


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Auto-play: link solto de música (YouTube/Spotify/SoundCloud) já
    # entra direto na fila, sem precisar de !tocar na frente.
    try:
        await _processar_link_solto(message)
    except Exception as e:
        print(f"[renan-musica] erro ao processar link solto de {message.author}: {e!r}")

    # Personalidade — respostas curtas e frias a gatilhos de conversa
    await _checar_personalidade(message)

    await bot.process_commands(message)


# ══════════════════════════════════════════════
# START
# ══════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(TOKEN)
