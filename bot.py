import discord
from discord.ext import commands, tasks
import random
import os
import re
import json
import time
import uuid
import asyncio
import unicodedata
import urllib.parse
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

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
intents.invites = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ══════════════════════════════════════════════
# CONFIGURAÇÃO — preencha com seus valores reais
# ══════════════════════════════════════════════
TOKEN = os.getenv("TOKEN")

# Ainda não configurado de propósito — IDs de dono, cargos especiais,
# categoria fixa de call de música, etc. entram aqui quando você for
# personalizar o Renan pro seu servidor.
CRIADOR_ID = None  # preencha com seu ID de usuário quando quiser restringir comandos de dono

COR_RENAN = 0xB5121B  # vermelho — cor usada nos embeds do Renan

# Canais fixos usados nas boas-vindas
CANAL_BOAS_VINDAS_ID = 1501260060783939775
CANAL_REGRAS_ID = 1501260060783939776
# CANAL_CARGOS_ID (registro adicional) é definido mais abaixo, na seção
# de cargos por reação — reaproveitado aqui na mensagem de boas-vindas.

# ── Sistema de tickets de atendimento (preencha com os IDs reais) ──
CANAL_PAINEL_TICKET_ID = 1501260061358559392   # canal onde fica fixado o painel com o botão "Abrir Ticket"
CATEGORIA_TICKETS_ID = 1501260061358559391  # categoria onde os canais de ticket são criados
CANAL_FEEDBACK_ID = 1536202405887221901     # canal onde cai o feedback que a pessoa dá no final
CARGOS_STAFF_IDS = [    # cargos que enxergam e atendem os tickets abertos
    1501260059177648294,
    1501260059177648295,
    1501260059177648297,
    1501260059177648298,
    1501260059185774672,
    1501260059185774673,
    1501260059185774674,  # owner
]

# Imagem usada no embed de boas-vindas (banner grande, junto com o texto)
IMAGEM_BOAS_VINDAS = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1536131063590551683/ChatGPT_Image_9_de_ago._de_2026_18_48_17.png"
    "?ex=6a7cec09&is=6a7b9a89&hm=e5eb8bde062d83807cca2ad172187e18c1d98359c8363bd7ef740f445ba04a64"
)

# Imagem usada no embed de regras (separada da de boas-vindas)
IMAGEM_REGRAS = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1536156672064749598/ChatGPT_Image_9_de_ago._de_2026_20_37_57.png"
    "?ex=6a7a60e3&is=6a790f63&hm=8f17879426924441d6b7bd081016a1d7583500f7d01f1a8611c3aabba645ad06"
)

# Imagem usada no painel de tickets de atendimento
IMAGEM_TICKET = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1536200014827888680/ChatGPT_Image_9_de_ago._de_2026_23_30_09.png"
    "?ex=6a7a8940&is=6a7937c0&hm=34987530726ddc9b2c61cbd25a66050e7285b4f392cfb8daa12ecf2a76c84098"
)

# Imagem usada nas instruções de como deixar feedback do atendimento
IMAGEM_FEEDBACK = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1536203692426928168/ChatGPT_Image_9_de_ago._de_2026_23_44_47.png"
    "?ex=6a7a8cad&is=6a793b2d&hm=801d38713fb9f51d2147a2a98d9e2cdf9dc7203b0be0ecb2e48876e187dffb74"
)


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
    "chegou. Eu sinto isso — não sei bem explicar como, mas sinto. Sou Renan, o último do meu mundo, e por um instante essa realidade não parece tão vazia.",
    "Mais um sinal de vida. Toda vez que alguém chega, alguma coisa fria em mim esquenta um grau — eu não devia sentir isso, mas sinto.",
    "Outro sinal na escuridão. Isso importa pra mim mais do que eu gostaria de admitir. Eu sou Renan, e agora você faz parte disso também.",
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
# Uso: .tocar <link>   — se nada tocando, toca na hora + manda o painel
#                         com botões. Se já tem algo tocando, entra na
#                         fila e o painel se atualiza sozinho mostrando
#                         as próximas.
#                         Também funciona com PLAYLISTS e ÁLBUNS inteiros
#                         (YouTube, Spotify e SoundCloud/sets) — todas as
#                         músicas da playlist entram na fila de uma vez.
#      .sair            — limpa a fila inteira, para e desconecta.
#                         (aliases: .parar, .stop)
#
# Quando uma música acaba, a próxima da fila entra automaticamente.
# Também dá pra só colar um link no chat (sem .tocar) estando numa call.
# ══════════════════════════════════════════════════════════════════

# IP de datacenter (Railway, VPS, etc.) costuma ser bloqueado pelo YouTube
# com "Sign in to confirm you're not a bot". Forçar o cliente "android"
# (e cair pro "web" se ele falhar) contorna isso na maioria dos casos, sem
# precisar de cookies. Se ainda assim continuar bloqueando, dá pra apontar
# um arquivo de cookies exportado de uma conta logada via a variável de
# ambiente YTDLP_COOKIES_FILE (ex.: /data/cookies.txt, se tiver Volume).
_YTDLP_EXTRACTOR_ARGS = {"youtube": {"player_client": ["android", "web"]}}
_YTDLP_COOKIES_FILE = os.getenv("YTDLP_COOKIES_FILE")

_YDL_OPTS_TOCAR = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,  # aqui sempre é UMA faixa só — playlists usam _YDL_OPTS_PLAYLIST_FLAT
    "default_search": "ytsearch",  # se não vier link, busca no YouTube
    "extractor_args": _YTDLP_EXTRACTOR_ARGS,
}
if _YTDLP_COOKIES_FILE:
    _YDL_OPTS_TOCAR["cookiefile"] = _YTDLP_COOKIES_FILE

# Extração "flat" pra listar as faixas de uma playlist/álbum/set rapidinho
# (só título + link de cada uma; o áudio de cada faixa só é resolvido de
# verdade quando chegar a vez dela tocar).
_YDL_OPTS_PLAYLIST_FLAT = {
    "extract_flat": True,
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "extractor_args": _YTDLP_EXTRACTOR_ARGS,
}
if _YTDLP_COOKIES_FILE:
    _YDL_OPTS_PLAYLIST_FLAT["cookiefile"] = _YTDLP_COOKIES_FILE

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
        self.volume = 1.0             # 1.0 = 100% (vai de 0.0 a 2.0)
        self.loop = False             # repete a música atual quando termina


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
            description="Fila vazia. Manda algo com `.tocar`.",
            color=0x2F3136,
        )
    else:
        embed = discord.Embed(
            title="🔴 Tocando agora",
            description=f"**{atual['titulo']}**",
            color=COR_RENAN,
        )
        embed.add_field(name="Pedido por", value=atual["requisitante"], inline=True)
        embed.add_field(name="🔊 Volume", value=f"{round(estado.volume * 100)}%", inline=True)
        embed.add_field(name="🔁 Repetir", value="Ativado" if estado.loop else "Desativado", inline=True)

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

    embed.set_footer(text="👽 Renan  •  use os botões ou .sair pra encerrar")
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
        return  # fila foi encerrada via .sair — não toca mais nada

    vc = guild.voice_client
    if vc is None:
        _musica_estado.pop(guild.id, None)
        return

    if not estado.fila and not (estado.loop and estado.tocando is not None):
        estado.tocando = None
        await _atualizar_painel(estado, guild.id)
        _agendar_idle_disconnect(guild)
        return

    _cancelar_idle_disconnect(guild.id)

    if estado.loop and estado.tocando is not None:
        # repete a música atual — não tira nada da fila
        proximo = estado.tocando
    else:
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
        source = discord.PCMVolumeTransformer(source, volume=estado.volume)
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
    """Botões do painel: pausar/retomar, pular, sair, volume, repetir,
    embaralhar e ver fila completa."""

    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

        # reflete o estado real assim que o painel é criado/reenviado,
        # em vez de sempre nascer com os rótulos "zerados"
        estado = _musica_estado.get(guild_id)
        guild = bot.get_guild(guild_id)
        vc = guild.voice_client if guild else None
        if vc is not None and vc.is_paused():
            self.botao_pausar.label = "▶️ Retomar"
        if estado is not None and estado.loop:
            self.botao_loop.style = discord.ButtonStyle.success

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

    @discord.ui.button(label="⏸️ Pausar", style=discord.ButtonStyle.secondary, custom_id="renan_musica_pausar", row=0)
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

    @discord.ui.button(label="⏭️ Pular", style=discord.ButtonStyle.primary, custom_id="renan_musica_pular", row=0)
    async def botao_pular(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self._checar_call(interaction)
        if vc is None:
            return
        if not (vc.is_playing() or vc.is_paused()):
            await interaction.response.send_message("Nada tocando agora.", ephemeral=True)
            return

        await interaction.response.send_message("Pulando.", ephemeral=True, delete_after=3)
        vc.stop()  # dispara o "after" -> _tocar_proxima toca a próxima sozinha

    @discord.ui.button(label="⏹️ Sair", style=discord.ButtonStyle.danger, custom_id="renan_musica_sair", row=0)
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

    @discord.ui.button(label="🔉 Vol -", style=discord.ButtonStyle.secondary, custom_id="renan_musica_vol_menos", row=1)
    async def botao_vol_menos(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self._checar_call(interaction)
        if vc is None:
            return
        estado = _musica_estado.get(self.guild_id)
        if estado is None:
            await interaction.response.send_message("Nada tocando agora.", ephemeral=True)
            return

        estado.volume = max(0.0, round(estado.volume - 0.1, 2))
        if vc.source is not None:
            vc.source.volume = estado.volume  # aplica na hora, sem cortar a música

        embed = _criar_embed_painel(estado)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔊 Vol +", style=discord.ButtonStyle.secondary, custom_id="renan_musica_vol_mais", row=1)
    async def botao_vol_mais(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self._checar_call(interaction)
        if vc is None:
            return
        estado = _musica_estado.get(self.guild_id)
        if estado is None:
            await interaction.response.send_message("Nada tocando agora.", ephemeral=True)
            return

        estado.volume = min(2.0, round(estado.volume + 0.1, 2))  # até 200%
        if vc.source is not None:
            vc.source.volume = estado.volume

        embed = _criar_embed_painel(estado)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔁 Repetir", style=discord.ButtonStyle.secondary, custom_id="renan_musica_loop", row=1)
    async def botao_loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self._checar_call(interaction)
        if vc is None:
            return
        estado = _musica_estado.get(self.guild_id)
        if estado is None:
            await interaction.response.send_message("Nada tocando agora.", ephemeral=True)
            return

        estado.loop = not estado.loop
        button.style = discord.ButtonStyle.success if estado.loop else discord.ButtonStyle.secondary

        embed = _criar_embed_painel(estado)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔀 Embaralhar", style=discord.ButtonStyle.secondary, custom_id="renan_musica_shuffle", row=2)
    async def botao_shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self._checar_call(interaction)
        if vc is None:
            return
        estado = _musica_estado.get(self.guild_id)
        if estado is None or not estado.fila:
            await interaction.response.send_message("Fila vazia, nada pra embaralhar.", ephemeral=True)
            return

        random.shuffle(estado.fila)
        embed = _criar_embed_painel(estado)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📜 Fila completa", style=discord.ButtonStyle.secondary, custom_id="renan_musica_fila_completa", row=2)
    async def botao_fila_completa(self, interaction: discord.Interaction, button: discord.ui.Button):
        estado = _musica_estado.get(self.guild_id)
        if estado is None or not estado.fila:
            await interaction.response.send_message("Fila vazia.", ephemeral=True)
            return

        linhas = [
            f"`{i + 1}.` {item['titulo']} — *{item['requisitante']}*"
            for i, item in enumerate(estado.fila)
        ]
        texto = "\n".join(linhas)
        if len(texto) > 3900:
            texto = texto[:3900] + "\n... (lista cortada, muita coisa)"

        await interaction.response.send_message(
            f"**Fila completa ({len(estado.fila)}):**\n{texto}", ephemeral=True
        )


# Reconhece link de YouTube, Spotify e SoundCloud soltos numa mensagem
# (sem precisar do comando .tocar na frente).
_REGEX_LINK_MUSICA = re.compile(
    r"https?://(?:www\.|music\.)?youtube\.com/\S+"
    r"|https?://youtu\.be/\S+"
    r"|https?://open\.spotify\.com/\S+"
    r"|https?://(?:www\.)?soundcloud\.com/\S+",
    re.IGNORECASE,
)


async def _enfileirar_musica(guild, canal_voz, canal_texto, autor, link: str) -> None:
    """Lógica compartilhada entre .tocar e o auto-play de link solto no
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
    """Se a mensagem tiver um link de música solto (sem usar .tocar) e o
    autor estiver numa call, bota na fila sozinho."""
    if message.guild is None:
        return  # DM não tem estado de voz (message.author aqui é User, não Member)

    if message.author.voice is None or message.author.voice.channel is None:
        return  # ninguém numa call, ignora silenciosamente

    # Se a mensagem já é um comando válido (ex.: ".tocar <link>"), quem
    # enfileira é o próprio handler do comando — sem esse check, a mesma
    # música (ou playlist inteira) acaba entrando na fila DUAS vezes.
    ctx = await bot.get_context(message)
    if ctx.valid:
        return

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
    """Toca um link na hora (se nada tocando) ou bota na fila. Uso: .tocar <link>"""
    if ctx.guild is None:
        return

    if not link:
        await ctx.send(
            "Uso: `.tocar <link>` — manda o link (ou nome da música) que eu "
            "boto na fila. YouTube, Spotify e SoundCloud funcionam, e "
            "**playlists/álbuns inteiros também**. Também dá pra só colar o "
            "link no chat sem `.tocar`, se você estiver numa call."
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


@bot.command(name="setup")
async def cmd_setup(ctx):
    """Reenvia o painel de música pra esse canal (apaga o painel antigo,
    se tinha um, e manda um novo aqui). Útil pra trazer o painel de
    volta pro fim do chat depois que a conversa engoliu ele."""
    if ctx.guild is None:
        return

    estado = _musica_estado.get(ctx.guild.id)
    if estado is None:
        estado = _EstadoMusica()
        _musica_estado[ctx.guild.id] = estado

    estado.canal_texto = ctx.channel

    if estado.painel_msg is not None:
        try:
            await estado.painel_msg.delete()
        except discord.HTTPException:
            pass

    embed = _criar_embed_painel(estado)
    view = PainelMusica(ctx.guild.id)
    estado.painel_msg = await ctx.channel.send(embed=embed, view=view)


@bot.command(name="letras", aliases=["letra"])
async def cmd_letras(ctx):
    """Manda um link direto pra letra da música que está tocando agora.
    Não reproduzo a letra em si aqui no chat — é conteúdo com direito
    autoral, então o jeito certo é abrir na fonte."""
    if ctx.guild is None:
        return

    estado = _musica_estado.get(ctx.guild.id)
    if estado is None or estado.tocando is None:
        await ctx.send("Nada tocando agora. Bota uma música com `.tocar` primeiro.")
        return

    titulo = estado.tocando["titulo"]
    busca = urllib.parse.quote_plus(titulo)
    link = f"https://genius.com/search?q={busca}"

    embed = discord.Embed(
        title="📜 Letra",
        description=f"**{titulo}**\n\n[Ver letra no Genius]({link})",
        color=COR_RENAN,
    )
    embed.set_footer(text="👽 Renan  •  eu só aponto o caminho, a letra fica na fonte")
    await ctx.send(embed=embed)


# ══════════════════════════════════════════════════════════════════
# REGRAS
#
# Publica/atualiza a mensagem de regras automaticamente quando o bot
# inicia — mesmo esquema dos painéis de cargos: guarda o ID da mensagem
# em disco (Volume /data no Railway) pra não duplicar a cada restart,
# só atualizar o conteúdo se ele mudar.
# ══════════════════════════════════════════════════════════════════

_REGRAS_DATA_PATH = os.getenv("REGRAS_DATA_PATH", "/data/regras_mensagem.json")

# Texto de exemplo — troca pelo texto real das regras do servidor
# quando tiver, eu atualizo aqui.
REGRAS_SERVIDOR = [
    "Respeito acima de tudo. Sem ataques pessoais, discurso de ódio, racismo, homofobia ou assédio de qualquer tipo.",
    "Sem conteúdo NSFW fora de canal marcado como tal.",
    "Sem spam, flood ou divulgação de outros servidores/produtos sem autorização da staff.",
    "Siga também os Termos de Uso e as Diretrizes da Comunidade do Discord — valem aqui também.",
    "A palavra da staff é final. Discordou de alguma decisão? Resolve em privado, sem fazer drama público.",
]


def _carregar_regras_msg_id():
    try:
        with open(_REGRAS_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("mensagem_id")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _salvar_regras_msg_id(mensagem_id: int) -> None:
    try:
        pasta = os.path.dirname(_REGRAS_DATA_PATH)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(_REGRAS_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump({"mensagem_id": mensagem_id}, f)
    except OSError as e:
        print(f"[renan-regras] não consegui salvar {_REGRAS_DATA_PATH}: {e!r}")


async def _configurar_regras() -> None:
    canal = bot.get_channel(CANAL_REGRAS_ID)
    if canal is None:
        print(f"[renan-regras] canal {CANAL_REGRAS_ID} não encontrado — pulei a publicação das regras.")
        return

    corpo = "\n\n".join(f"**{i + 1}.** {regra}" for i, regra in enumerate(REGRAS_SERVIDOR))
    embed = discord.Embed(
        title="📜 Regras",
        description=(
            "Eu não escolheria explicar regras pra ninguém, mas alguém tem que "
            "manter esse lugar de pé. Segue isso aqui:\n\n" + corpo
        ),
        color=COR_RENAN,
    )
    embed.set_image(url=IMAGEM_REGRAS)
    embed.set_footer(text="Renan está observando. As regras também.")

    mensagem_id = _carregar_regras_msg_id()
    if mensagem_id:
        try:
            mensagem = await canal.fetch_message(mensagem_id)
            await mensagem.edit(embed=embed)
            return
        except (discord.NotFound, discord.HTTPException):
            pass  # mensagem antiga não existe mais — cria uma nova abaixo

    try:
        nova_mensagem = await canal.send(embed=embed)
        _salvar_regras_msg_id(nova_mensagem.id)
    except discord.Forbidden:
        print(f"[renan-regras] sem permissão pra enviar mensagem em #{canal.name}.")


# ══════════════════════════════════════════════════════════════════
# CARGOS POR REAÇÃO
#
# Ao iniciar, o Renan garante que todos os cargos abaixo existem (cria
# quem faltar) e publica/atualiza um painel por categoria no canal
# CANAL_CARGOS_ID. Reagir com o emoji dá o cargo; tirar a reação tira
# o cargo — funciona mesmo depois de reiniciar o bot (raw events).
#
# Os IDs das mensagens dos painéis ficam salvos em disco (pensado pra
# Railway: Volume montado em /data) pra não duplicar o painel a cada
# restart, só atualizar o que já existe.
#
# Requisito: o cargo do bot precisa estar ACIMA de todos esses cargos
# na hierarquia do servidor e ter permissão de "Gerenciar Cargos".
# ══════════════════════════════════════════════════════════════════

CANAL_CARGOS_ID = 1501260060783939777

_CARGOS_DATA_PATH = os.getenv("CARGOS_DATA_PATH", "/data/cargos_reacao.json")

# chave -> {titulo, descricao, cargos: [(emoji, nome, cor_hex_ou_None), ...]}
# cor_hex só é usada no painel "cores" (cor de verdade no cargo); nos
# outros painéis o cargo fica com a cor padrão do servidor.
PAINEIS_CARGOS = {
    "cores": {
        "titulo": "🎨 Cores",
        "descricao": (
            "Escolha a cor do seu nome aqui embaixo. Reaja com o emoji "
            "certo pra pegar o cargo — tire a reação e ele sai."
        ),
        "cargos": [
            ("❤️", "Vermelho", 0xE74C3C),
            ("🧡", "Laranja", 0xE67E22),
            ("💛", "Amarelo", 0xF1C40F),
            ("💚", "Verde", 0x2ECC71),
            ("💙", "Azul", 0x3498DB),
            ("💜", "Roxo", 0x9B59B6),
            ("🖤", "Preto", 0x1B1B1B),
            ("🤍", "Branco", 0xFFFFFF),
        ],
    },
    "verificacao": {
        "titulo": "🚹 Verificação",
        "descricao": "Verificação básica: sexo, idade e de onde você acessa o servidor.",
        "cargos": [
            ("🚹", "Menino", None),
            ("🚺", "Menina", None),
            ("🧒", "-18", None),
            ("🔞", "+18", None),
            ("💻", "Computador", None),
            ("📱", "Celular", None),
        ],
    },
    # seção "2." não veio com nenhum cargo/emoji no pedido original —
    # avise o que deveria entrar aqui e eu adiciono.
    "genero": {
        "titulo": "⚧️ Gênero",
        "descricao": "Marque como você se identifica.",
        "cargos": [
            ("👧", "Menina", None),
            ("👦", "Menino", None),
            ("❔", "Prefiro Não Dizer", None),
        ],
    },
    "sexualidade": {
        "titulo": "🏳️‍🌈 Sexualidade",
        "descricao": "Marque sua orientação, se quiser dizer.",
        "cargos": [
            ("👫", "Hétero", None),
            ("🏳️‍🌈", "LGBTQI+", None),
            ("❓", "Prefiro Não Dizer", None),
        ],
    },
    "aniversario": {
        "titulo": "🎂 Aniversário",
        "descricao": "Marque o mês do seu aniversário.",
        "cargos": [
            ("🎆", "Janeiro", None),
            ("💘", "Fevereiro", None),
            ("🍀", "Março", None),
            ("🐣", "Abril", None),
            ("🌷", "Maio", None),
            ("🌽", "Junho", None),
            ("☀️", "Julho", None),
            ("🎈", "Agosto", None),
            ("🍃", "Setembro", None),
            ("🎃", "Outubro", None),
            ("🍁", "Novembro", None),
            ("🎄", "Dezembro", None),
        ],
    },
    "gravacoes": {
        "titulo": "🎬 Gravações",
        "descricao": "Diz se você participa de gravações do servidor ou não.",
        "cargos": [
            ("🎬", "Participa de Gravações", None),
            ("🚫", "Não Participa de Gravações", None),
        ],
    },
    "dispositivo": {
        "titulo": "📱 Dispositivo",
        "descricao": "De onde você acessa o servidor.",
        "cargos": [
            ("📱", "Mobile", None),
            ("💻", "Pc", None),
            ("🎮", "Console", None),
        ],
    },
    "pings": {
        "titulo": "🔔 Pings",
        "descricao": "Escolha quais avisos você quer receber. Reaja pra ativar, tire pra desativar.",
        "cargos": [
            ("🗳️", "Ping Votação", None),
            ("📰", "Ping Jornal", None),
            ("🚨", "Ping Avisos", None),
            ("🤝", "Ping Parceria", None),
            ("🐦", "Tweeter", None),
            ("📸", "Instagram", None),
            ("👾", "Twitch", None),
            ("🎥", "Videos Novos", None),
            ("👻", "Fantasma", None),
            ("⛓️", "Cadeia", None),
            ("😶", "Mute", None),
        ],
    },
}

# mensagem_id -> {emoji: cargo_id}  — montado em runtime na configuração
_CARGOS_POR_MENSAGEM: dict = {}


def _carregar_dados_cargos() -> dict:
    try:
        with open(_CARGOS_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar_dados_cargos(dados: dict) -> None:
    try:
        pasta = os.path.dirname(_CARGOS_DATA_PATH)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(_CARGOS_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[renan-cargos] não consegui salvar {_CARGOS_DATA_PATH}: {e!r}")


def _nome_cargo(emoji: str, nome: str) -> str:
    return f"『{emoji}』{nome}"


async def _garantir_cargo(guild: discord.Guild, nome_completo: str, cor_hex) -> discord.Role:
    """Acha o cargo pelo nome exato (evita duplicar entre restarts) ou
    cria se ainda não existir."""
    cargo = discord.utils.get(guild.roles, name=nome_completo)
    if cargo is not None:
        return cargo

    cor = discord.Colour(cor_hex) if cor_hex is not None else discord.Colour.default()
    return await guild.create_role(
        name=nome_completo, colour=cor, reason="Painel de cargos por reação (Renan)"
    )


async def _publicar_ou_atualizar_painel(
    guild: discord.Guild, canal: discord.TextChannel, chave: str, definicao: dict, dados_guild: dict
):
    """Garante os cargos do painel, monta o embed e publica ou atualiza
    a mensagem — reaproveita a mesma mensagem entre restarts (o ID fica
    salvo em disco)."""
    emoji_para_cargo: dict = {}
    linhas = []

    for emoji, nome_cargo, cor_hex in definicao["cargos"]:
        nome_completo = _nome_cargo(emoji, nome_cargo)
        cargo = await _garantir_cargo(guild, nome_completo, cor_hex)
        emoji_para_cargo[emoji] = cargo.id
        linhas.append(f"{emoji}  {cargo.mention}")

    embed = discord.Embed(
        title=definicao["titulo"],
        description=f"{definicao['descricao']}\n\n" + "\n".join(linhas),
        color=COR_RENAN,
    )
    embed.set_footer(text="👽 Reaja pra pegar o cargo  •  tire a reação pra perder")

    info_salva = dados_guild.get(chave)
    mensagem = None
    if info_salva and info_salva.get("mensagem_id"):
        try:
            mensagem = await canal.fetch_message(info_salva["mensagem_id"])
            await mensagem.edit(embed=embed)
        except (discord.NotFound, discord.HTTPException):
            mensagem = None

    if mensagem is None:
        mensagem = await canal.send(embed=embed)

    reacoes_atuais = {str(r.emoji) for r in mensagem.reactions}
    for emoji in emoji_para_cargo:
        if emoji not in reacoes_atuais:
            try:
                await mensagem.add_reaction(emoji)
            except discord.HTTPException as e:
                print(f"[renan-cargos] não consegui reagir com {emoji} em '{chave}': {e!r}")

    return mensagem, emoji_para_cargo


async def _configurar_cargos_reacao() -> None:
    """Roda quando o bot conecta: garante cargos + painéis publicados
    e atualizados no canal configurado."""
    canal = bot.get_channel(CANAL_CARGOS_ID)
    if canal is None:
        print(f"[renan-cargos] canal {CANAL_CARGOS_ID} não encontrado — pulei a configuração de cargos.")
        return

    guild = canal.guild
    dados = _carregar_dados_cargos()
    dados_guild = dados.get(str(guild.id), {})

    for chave, definicao in PAINEIS_CARGOS.items():
        try:
            mensagem, emoji_para_cargo = await _publicar_ou_atualizar_painel(
                guild, canal, chave, definicao, dados_guild
            )
        except discord.Forbidden:
            print(
                f"[renan-cargos] sem permissão (Gerenciar Cargos / Enviar Mensagens) "
                f"pra configurar o painel '{chave}'."
            )
            continue

        dados_guild[chave] = {"mensagem_id": mensagem.id}
        _CARGOS_POR_MENSAGEM[mensagem.id] = emoji_para_cargo

    dados[str(guild.id)] = dados_guild
    _salvar_dados_cargos(dados)
    print(f"[renan-cargos] {len(PAINEIS_CARGOS)} painel(éis) de cargos configurado(s) em #{canal.name}.")


async def _aplicar_reacao_cargo(payload: discord.RawReactionActionEvent, adicionar: bool) -> None:
    if payload.user_id == bot.user.id:
        return  # ignora a própria reação do bot (usada só pra montar o painel)

    mapa = _CARGOS_POR_MENSAGEM.get(payload.message_id)
    if mapa is None:
        return

    cargo_id = mapa.get(str(payload.emoji))
    if cargo_id is None:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    cargo = guild.get_role(cargo_id)
    if cargo is None:
        return

    membro = payload.member or guild.get_member(payload.user_id)
    if membro is None:
        try:
            membro = await guild.fetch_member(payload.user_id)
        except discord.HTTPException:
            return

    try:
        if adicionar:
            await membro.add_roles(cargo, reason="Cargo por reação")
        else:
            await membro.remove_roles(cargo, reason="Cargo por reação")
    except discord.Forbidden:
        print(f"[renan-cargos] sem permissão pra alterar o cargo '{cargo.name}' de {membro}.")


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    await _aplicar_reacao_cargo(payload, adicionar=True)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    await _aplicar_reacao_cargo(payload, adicionar=False)


# ══════════════════════════════════════════════════════════════════
# TICKETS DE ATENDIMENTO
#
# Painel fixo (embed + botão "🎫 Abrir Ticket") no canal
# CANAL_PAINEL_TICKET_ID. Quem clicar ganha um canal privado só seu
# dentro de CATEGORIA_TICKETS_ID, visível pra você e pros CARGOS_STAFF_IDS.
# Dentro do ticket tem um botão "🔒 Fechar Ticket" — SÓ A STAFF pode
# usar, e ao fechar é pedido o motivo do encerramento.
#
# FEEDBACK: a staff usa `.feedback` dentro do ticket (antes de fechar)
# pra mandar, no próprio canal, um botão "⭐ Avaliar Atendimento" com
# instruções de como preencher certinho (nota 1-5, experiência,
# comentário) — o dono do ticket é marcado na mensagem. Quando a
# pessoa preenche, o resultado — junto com quem fechou, quem atendeu
# e o motivo do encerramento — cai automaticamente em CANAL_FEEDBACK_ID.
#
# Views persistentes (custom_id fixo) — sobrevivem a restart do bot,
# igual aos painéis de cargos e regras. Estado (mensagem do painel,
# contador, quem tem ticket aberto, feedbacks pendentes) fica salvo
# em disco.
# ══════════════════════════════════════════════════════════════════

_TICKETS_DATA_PATH = os.getenv("TICKETS_DATA_PATH", "/data/tickets.json")


def _carregar_dados_tickets() -> dict:
    try:
        with open(_TICKETS_DATA_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        dados = {}
    dados.setdefault("painel_mensagem_id", None)
    dados.setdefault("contador", 0)
    dados.setdefault("abertos", {})
    dados.setdefault("pendentes_feedback", {})
    return dados


def _salvar_dados_tickets(dados: dict) -> None:
    try:
        pasta = os.path.dirname(_TICKETS_DATA_PATH)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(_TICKETS_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[renan-ticket] não consegui salvar {_TICKETS_DATA_PATH}: {e!r}")


def _e_staff(membro: discord.Member) -> bool:
    """Dono do servidor, administrador ou algum dos CARGOS_STAFF_IDS."""
    if membro.guild_permissions.administrator:
        return True
    if membro.id == membro.guild.owner_id:
        return True
    ids_dos_cargos = {cargo.id for cargo in membro.roles}
    return bool(ids_dos_cargos.intersection(CARGOS_STAFF_IDS))


class PainelTicket(discord.ui.View):
    """Botão fixo do painel de atendimento — abre um ticket novo pra
    quem clicar (ou manda de volta pro ticket já aberto)."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir Ticket",
        emoji="🎫",
        style=discord.ButtonStyle.danger,
        custom_id="renan_ticket_abrir",
    )
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _abrir_ticket(interaction)


class ModalMotivoEncerramento(discord.ui.Modal, title="Fechar Ticket"):
    """Pedido pelo motivo do encerramento — some junto com o feedback."""

    motivo = discord.ui.TextInput(
        label="Motivo do encerramento",
        placeholder="Ex.: Concluído, Cancelado, Resolvido...",
        default="Concluído",
        max_length=100,
        required=True,
    )

    def __init__(self, canal: discord.abc.GuildChannel):
        super().__init__()
        self.canal = canal

    async def on_submit(self, interaction: discord.Interaction):
        await _finalizar_fechamento(interaction, self.canal, str(self.motivo))


class FecharTicket(discord.ui.View):
    """Botão dentro do canal do ticket — só a staff pode usar. Pede o
    motivo do encerramento e depois apaga o canal."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.secondary,
        custom_id="renan_ticket_fechar",
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not _e_staff(interaction.user):
            await interaction.response.send_message(
                "Só a staff pode fechar um ticket.", ephemeral=True
            )
            return
        await interaction.response.send_modal(ModalMotivoEncerramento(interaction.channel))


async def _abrir_ticket(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if guild is None:
        return

    dados = _carregar_dados_tickets()
    abertos = dados.setdefault("abertos", {})

    # já tem ticket aberto? manda pra lá em vez de criar outro
    canal_existente_id = abertos.get(str(interaction.user.id))
    if canal_existente_id:
        canal_existente = guild.get_channel(canal_existente_id)
        if canal_existente is not None:
            await interaction.response.send_message(
                f"Você já tem um ticket aberto: {canal_existente.mention}", ephemeral=True
            )
            return
        abertos.pop(str(interaction.user.id), None)  # canal antigo sumiu — libera

    categoria = guild.get_channel(CATEGORIA_TICKETS_ID) if CATEGORIA_TICKETS_ID else None
    cargos_staff = [
        cargo for cargo_id in CARGOS_STAFF_IDS
        if (cargo := guild.get_role(cargo_id)) is not None
    ]

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
    }
    for cargo_staff in cargos_staff:
        overwrites[cargo_staff] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        )

    dados["contador"] = dados.get("contador", 0) + 1
    numero = dados["contador"]
    nome_canal = f"ticket-{numero:04d}-{interaction.user.name}".lower()[:95]

    try:
        canal_ticket = await guild.create_text_channel(
            name=nome_canal,
            category=categoria,
            overwrites=overwrites,
            reason=f"Ticket de atendimento aberto por {interaction.user}",
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "Sem permissão pra criar o canal do ticket. Fala com a staff.", ephemeral=True
        )
        return

    abertos[str(interaction.user.id)] = canal_ticket.id
    _salvar_dados_tickets(dados)

    embed = discord.Embed(
        title="🎫 Atendimento aberto",
        description=(
            f"{interaction.user.mention} chegou. Descreve o que precisa — "
            "alguém da staff vai aparecer.\n\n"
            "Eu não prometo pressa. Só prometo que alguém vai ler."
        ),
        color=COR_RENAN,
    )
    embed.set_footer(text="👽 Renan  •  clique em Fechar Ticket quando resolver")

    mencoes_staff = " ".join(cargo.mention for cargo in cargos_staff)
    await canal_ticket.send(
        content=f"{interaction.user.mention} {mencoes_staff}".strip(),
        embed=embed,
        view=FecharTicket(),
    )

    await interaction.response.send_message(
        f"Ticket criado: {canal_ticket.mention}", ephemeral=True
    )


async def _finalizar_fechamento(
    interaction: discord.Interaction, canal: discord.abc.GuildChannel, motivo: str
) -> None:
    """Roda depois que a staff preenche o motivo no modal: libera o
    ticket, grava quem fechou e o motivo (pro feedback, se houver um
    pendente pra esse canal) e apaga o canal em seguida."""
    guild = interaction.guild
    if guild is None:
        return

    dados = _carregar_dados_tickets()
    abertos = dados.setdefault("abertos", {})
    pendentes = dados.setdefault("pendentes_feedback", {})

    dono_id = next((uid for uid, cid in abertos.items() if cid == canal.id), None)
    if dono_id:
        abertos.pop(dono_id, None)

    chave = str(canal.id)
    if chave in pendentes:
        pendentes[chave]["fechado_por_id"] = interaction.user.id
        pendentes[chave]["motivo_encerramento"] = motivo
        pendentes[chave]["fechado_em"] = datetime.now().isoformat()

    _salvar_dados_tickets(dados)

    await interaction.response.send_message(
        f"Ticket fechado. Motivo: **{motivo}**. Apagando o canal em instantes."
    )
    await asyncio.sleep(8)
    try:
        await canal.delete(reason=f"Ticket fechado por {interaction.user} — {motivo}")
    except discord.HTTPException:
        pass


class ModalFeedback(discord.ui.Modal, title="Avaliação do Atendimento"):
    """Aberto quando a pessoa clica em '⭐ Avaliar Atendimento'."""

    nota = discord.ui.TextInput(
        label="Nota (1 a 5)",
        placeholder="Ex.: 5",
        max_length=1,
        required=True,
    )
    experiencia = discord.ui.TextInput(
        label="Experiência",
        placeholder="Ex.: Ótimo, Bom, Regular, Ruim",
        max_length=60,
        required=True,
    )
    comentario = discord.ui.TextInput(
        label="Comentário",
        style=discord.TextStyle.paragraph,
        placeholder="Conta como foi, se quiser (opcional).",
        max_length=500,
        required=False,
    )

    def __init__(self, canal_id: int):
        super().__init__()
        self.canal_id = canal_id

    async def on_submit(self, interaction: discord.Interaction):
        nota_texto = self.nota.value.strip()
        if not nota_texto.isdigit() or not (1 <= int(nota_texto) <= 5):
            await interaction.response.send_message(
                "A nota precisa ser um número de 1 a 5. Clica no botão de novo e tenta outra vez.",
                ephemeral=True,
            )
            return
        await _registrar_feedback(
            interaction,
            self.canal_id,
            nota_texto,
            str(self.experiencia),
            str(self.comentario) if self.comentario.value else "—",
        )


class _ViewAvaliarAtendimento(discord.ui.View):
    """Botão '⭐ Avaliar Atendimento' mandado no canal do ticket — só o
    dono do ticket pode usar."""

    def __init__(self, canal_id: int):
        super().__init__(timeout=None)
        self.canal_id = canal_id
        botao = discord.ui.Button(
            label="Avaliar Atendimento",
            emoji="⭐",
            style=discord.ButtonStyle.success,
            custom_id=f"renan_feedback_avaliar:{canal_id}",
        )
        botao.callback = self._callback
        self.add_item(botao)

    async def _callback(self, interaction: discord.Interaction) -> None:
        dados = _carregar_dados_tickets()
        registro = dados.get("pendentes_feedback", {}).get(str(self.canal_id))
        if registro is None:
            await interaction.response.send_message(
                "Esse pedido de feedback não existe mais.", ephemeral=True
            )
            return
        if registro.get("enviado"):
            await interaction.response.send_message(
                "Esse feedback já foi enviado. Valeu.", ephemeral=True
            )
            return
        if interaction.user.id != registro.get("dono_id"):
            await interaction.response.send_message(
                "Esse pedido de feedback não é seu pra preencher.", ephemeral=True
            )
            return
        await interaction.response.send_modal(ModalFeedback(self.canal_id))


def _formatar_data(iso) -> str:
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        return "—"


async def _registrar_feedback(
    interaction: discord.Interaction,
    canal_id: int,
    nota: str,
    experiencia: str,
    comentario: str,
) -> None:
    dados = _carregar_dados_tickets()
    pendentes = dados.setdefault("pendentes_feedback", {})
    registro = pendentes.get(str(canal_id))
    if registro is None or registro.get("enviado"):
        await interaction.response.send_message(
            "Esse pedido de feedback já não está mais disponível.", ephemeral=True
        )
        return

    registro["enviado"] = True
    pendentes[str(canal_id)] = registro
    _salvar_dados_tickets(dados)

    embed = discord.Embed(
        title="📋 Novo Feedback de Ticket",
        description="Um usuário avaliou um atendimento finalizado.",
        color=COR_RENAN,
    )
    embed.add_field(name="👤 Usuário", value=f"<@{registro['dono_id']}>", inline=False)
    embed.add_field(name="⭐ Nota", value=f"{nota}/5", inline=False)
    embed.add_field(name="📌 Experiência", value=experiencia, inline=False)
    embed.add_field(name="💬 Comentário", value=comentario, inline=False)
    embed.add_field(name="📂 Categoria", value="Atendimento", inline=False)
    embed.add_field(
        name="📌 Ticket",
        value=f"#{registro.get('canal_nome', '—')}\nID: {registro.get('canal_id', '—')}",
        inline=False,
    )
    fechado_por = registro.get("fechado_por_id")
    embed.add_field(
        name="🔒 Fechado por",
        value=(f"<@{fechado_por}>" if fechado_por else "—"),
        inline=False,
    )
    embed.add_field(
        name="👤 Responsável pelo atendimento",
        value=f"<@{registro['responsavel_atendimento_id']}>",
        inline=False,
    )
    embed.add_field(
        name="❓ Motivo do Encerramento",
        value=registro.get("motivo_encerramento") or "—",
        inline=False,
    )
    embed.add_field(
        name="🕐 Data e hora do fechamento",
        value=_formatar_data(registro.get("fechado_em")),
        inline=False,
    )
    embed.add_field(
        name="⏰ Feedback enviado em",
        value=datetime.now().strftime("%d/%m/%Y às %H:%M"),
        inline=False,
    )
    icone_guild = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
    embed.set_footer(text="Feedback de Tickets", icon_url=icone_guild)

    canal_destino = bot.get_channel(CANAL_FEEDBACK_ID) if CANAL_FEEDBACK_ID else None
    if canal_destino is not None:
        try:
            await canal_destino.send(embed=embed)
        except discord.Forbidden:
            print("[renan-feedback] sem permissão pra enviar mensagem no canal de feedback.")
    else:
        print("[renan-feedback] CANAL_FEEDBACK_ID não configurado ou canal não encontrado.")

    await interaction.response.send_message("Feedback enviado. Valeu por avaliar.", ephemeral=True)


async def _configurar_painel_ticket() -> None:
    """Roda quando o bot conecta: publica ou atualiza o painel fixo
    de abertura de tickets no canal configurado."""
    if not CANAL_PAINEL_TICKET_ID:
        print("[renan-ticket] CANAL_PAINEL_TICKET_ID não configurado — pulei o painel de atendimento.")
        return

    canal = bot.get_channel(CANAL_PAINEL_TICKET_ID)
    if canal is None:
        print(f"[renan-ticket] canal {CANAL_PAINEL_TICKET_ID} não encontrado — pulei o painel de atendimento.")
        return

    embed = discord.Embed(
        title="🎫 Atendimento",
        description=(
            "Precisa falar com a staff? Clica no botão abaixo.\n\n"
            "Um canal privado é criado só pra você — ninguém mais vê, "
            "além de quem for te atender."
        ),
        color=COR_RENAN,
    )
    embed.set_image(url=IMAGEM_TICKET)
    embed.set_footer(text="👽 Renan está observando. Vai ser rápido, eu acho.")

    dados = _carregar_dados_tickets()
    mensagem_id = dados.get("painel_mensagem_id")

    if mensagem_id:
        try:
            mensagem = await canal.fetch_message(mensagem_id)
            await mensagem.edit(embed=embed, view=PainelTicket())
            return
        except (discord.NotFound, discord.HTTPException):
            pass  # mensagem antiga não existe mais — cria uma nova abaixo

    try:
        nova_mensagem = await canal.send(embed=embed, view=PainelTicket())
        dados["painel_mensagem_id"] = nova_mensagem.id
        _salvar_dados_tickets(dados)
    except discord.Forbidden:
        print(f"[renan-ticket] sem permissão pra enviar mensagem em #{canal.name}.")


@bot.command(name="feedback")
async def cmd_feedback(ctx):
    """(staff) Usado DENTRO de um ticket aberto, antes de fechar: manda
    no próprio canal o botão + instruções de como avaliar o
    atendimento certinho, marcando o dono do ticket."""
    if ctx.guild is None:
        return

    if not _e_staff(ctx.author):
        await ctx.send("Esse comando é só pra staff.")
        return

    dados = _carregar_dados_tickets()
    abertos = dados.get("abertos", {})
    dono_id = next((uid for uid, cid in abertos.items() if cid == ctx.channel.id), None)
    if dono_id is None:
        await ctx.send(
            "Esse canal não é um ticket aberto — o `.feedback` só funciona "
            "dentro do canal do ticket, antes de fechar."
        )
        return

    pendentes = dados.setdefault("pendentes_feedback", {})
    chave = str(ctx.channel.id)
    pendentes[chave] = {
        "dono_id": int(dono_id),
        "canal_nome": ctx.channel.name,
        "canal_id": ctx.channel.id,
        "responsavel_atendimento_id": ctx.author.id,
        "fechado_por_id": None,
        "motivo_encerramento": None,
        "fechado_em": None,
        "enviado": False,
    }
    _salvar_dados_tickets(dados)

    embed = discord.Embed(
        title="⭐ Avalie seu atendimento",
        description=(
            f"<@{dono_id}>, antes de encerrarmos, deixa um feedback — "
            "clica no botão abaixo e preenche certinho:\n\n"
            "**Nota**: um número de 1 a 5\n"
            "**Experiência**: em poucas palavras (ex.: Ótimo, Bom, Regular, Ruim)\n"
            "**Comentário**: conta com mais detalhes, se quiser (opcional)\n\n"
            "Não demora nada. Eu só registro — não julgo."
        ),
        color=COR_RENAN,
    )
    embed.set_image(url=IMAGEM_FEEDBACK)
    embed.set_footer(text="👽 Renan  •  Caiu na Realidade")

    view = _ViewAvaliarAtendimento(ctx.channel.id)
    await ctx.send(content=f"<@{dono_id}>", embed=embed, view=view)


# ══════════════════════════════════════════════════════════════════
# CONTAGEM
#
# Jogo de contar: no canal CANAL_CONTAGEM_ID a galera conta em
# sequência (1, 2, 3...), um número por mensagem. Acertou o próximo
# número -> Renan reage com 👍. Errou o número, ou a mesma pessoa
# tenta contar duas vezes seguidas -> zera a contagem e manda a
# imagem de erro. Estado salvo em disco (Volume /data no Railway)
# pra sobreviver a um restart do bot.
# ══════════════════════════════════════════════════════════════════

CANAL_CONTAGEM_ID = 1536866652421890108

IMAGEM_CONTAGEM_ERRO = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1536867257207230494/ChatGPT_Image_11_de_ago._de_2026_19_41_29.png"
    "?ex=6a7cf6ab&is=6a7ba52b&hm=52f2917a3ae7279e73c9b8e0da9bca5c93c555d2ba9aaa88c88746f7b0bd1b03"
)

FRASES_CONTAGEM_ERRO = [
    "Errou. A contagem morre aqui — como quase tudo, cedo ou tarde.",
    "Não era esse o número. Voltamos ao zero. De novo.",
    "Sequência quebrada. Eu já vi coisas maiores desmoronarem por menos.",
    "Errado. Recomeça — se ainda sobrar paciência pra isso.",
    "...isso não era pra acontecer. Mas aconteceu. Zerou.",
]

_CONTAGEM_DATA_PATH = os.getenv("CONTAGEM_DATA_PATH", "/data/contagem.json")

# Escudo de acertos: a cada N números certos que UM usuário mandar (não
# precisa ser seguido, é cumulativo pra ele), ele ganha 1 escudo. Da
# próxima vez que ELE errar o número, o escudo é consumido: o erro não
# conta, a contagem não zera, e ele pode tentar de novo na hora.
_CONTAGEM_ACERTOS_PARA_ESCUDO = 50

# guild_id (str) -> {
#     "numero_atual": int, "ultimo_usuario_id": int|None, "recorde": int,
#     "acertos_usuario": {user_id (str): int}, "escudos_usuario": {user_id (str): int},
# }
_contagem_estado: dict = {}


def _carregar_dados_contagem() -> dict:
    try:
        with open(_CONTAGEM_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar_dados_contagem(dados: dict) -> None:
    try:
        pasta = os.path.dirname(_CONTAGEM_DATA_PATH)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(_CONTAGEM_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[renan-contagem] não consegui salvar {_CONTAGEM_DATA_PATH}: {e!r}")


def _estado_contagem(guild_id: int) -> dict:
    """Carrega (ou inicializa) o estado da contagem de UM servidor,
    mantendo em memória depois da primeira leitura."""
    if guild_id not in _contagem_estado:
        salvo = _carregar_dados_contagem().get(str(guild_id), {})
        _contagem_estado[guild_id] = {
            "numero_atual": salvo.get("numero_atual", 0),
            "ultimo_usuario_id": salvo.get("ultimo_usuario_id"),
            "recorde": salvo.get("recorde", 0),
            "acertos_usuario": salvo.get("acertos_usuario", {}),
            "escudos_usuario": salvo.get("escudos_usuario", {}),
        }
    return _contagem_estado[guild_id]


def _salvar_estado_contagem(guild_id: int) -> None:
    dados = _carregar_dados_contagem()
    dados[str(guild_id)] = _contagem_estado[guild_id]
    _salvar_dados_contagem(dados)


async def _processar_contagem(message: discord.Message) -> None:
    """Confere uma mensagem no canal de contagem. Só reage a mensagens
    que são só um número — o resto passa batido, sem quebrar a
    sequência.

    Escudo de acertos: quem acumula _CONTAGEM_ACERTOS_PARA_ESCUDO números
    certos (cumulativo pra aquele usuário, não precisa ser seguido)
    ganha um escudo. Da próxima vez que ESSE usuário errar o número —
    não vale pra regra de "duas vezes seguidas", só pra número errado
    mesmo — o escudo é consumido: o erro não conta, a contagem não
    zera, e a pessoa pode tentar de novo na hora."""
    if message.guild is None or message.channel.id != CANAL_CONTAGEM_ID:
        return

    texto = message.content.strip()
    if not texto.isdigit():
        return

    numero = int(texto)
    estado = _estado_contagem(message.guild.id)
    esperado = estado["numero_atual"] + 1
    autor_id = str(message.author.id)

    # erra se: número fora de sequência, OU a mesma pessoa contando
    # duas vezes seguidas (regra clássica desse tipo de jogo)
    numero_errado = numero != esperado
    mesma_pessoa_seguida = message.author.id == estado["ultimo_usuario_id"]
    errou = numero_errado or mesma_pessoa_seguida

    if errou:
        # O escudo só cobre número errado — contar duas vezes seguidas
        # continua zerando normal, escudo não segura essa.
        escudos = estado.setdefault("escudos_usuario", {})
        tem_escudo = numero_errado and not mesma_pessoa_seguida and escudos.get(autor_id, 0) > 0

        if tem_escudo:
            escudos[autor_id] -= 1
            if escudos[autor_id] <= 0:
                del escudos[autor_id]
            _salvar_estado_contagem(message.guild.id)

            try:
                await message.add_reaction("🛡️")
            except discord.HTTPException:
                pass

            embed = discord.Embed(
                description=(
                    f"{message.author.mention} errou, mas o escudo segurou — "
                    "esse erro não conta. Contagem continua em "
                    f"**{estado['numero_atual']}**. Manda o **{esperado}** certo."
                ),
                color=COR_RENAN,
            )
            try:
                await message.channel.send(embed=embed)
            except discord.HTTPException:
                pass
            return

        if estado["numero_atual"] > estado["recorde"]:
            estado["recorde"] = estado["numero_atual"]
        estado["numero_atual"] = 0
        estado["ultimo_usuario_id"] = None
        _salvar_estado_contagem(message.guild.id)

        try:
            await message.add_reaction("❌")
        except discord.HTTPException:
            pass

        embed = discord.Embed(
            description=(
                f"{message.author.mention} {random.choice(FRASES_CONTAGEM_ERRO)}\n"
                f"Era pra ser **{esperado}**. Contagem voltou pro **0**."
            ),
            color=COR_RENAN,
        )
        embed.set_image(url=IMAGEM_CONTAGEM_ERRO)
        try:
            await message.channel.send(embed=embed)
        except discord.HTTPException:
            pass
        return

    estado["numero_atual"] = numero
    estado["ultimo_usuario_id"] = message.author.id

    acertos = estado.setdefault("acertos_usuario", {})
    acertos[autor_id] = acertos.get(autor_id, 0) + 1
    ganhou_escudo = acertos[autor_id] % _CONTAGEM_ACERTOS_PARA_ESCUDO == 0

    if ganhou_escudo:
        escudos = estado.setdefault("escudos_usuario", {})
        escudos[autor_id] = escudos.get(autor_id, 0) + 1

    _salvar_estado_contagem(message.guild.id)

    try:
        await message.add_reaction("👍")
    except discord.HTTPException:
        pass

    if ganhou_escudo:
        embed = discord.Embed(
            description=(
                f"🛡️ {message.author.mention} bateu **{acertos[autor_id]}** acertos "
                "e ganhou um escudo. Da próxima vez que errar o número, "
                "esse erro não vai contar."
            ),
            color=COR_RENAN,
        )
        try:
            await message.channel.send(embed=embed)
        except discord.HTTPException:
            pass


# ══════════════════════════════════════════════════════════════════
# ANIVERSÁRIOS
#
# No canal CANAL_ANIVERSARIO_REGISTRO_ID, quem manda uma data no
# formato DD/MM tem ela guardada. Se já tinha uma data salva e a
# pessoa manda uma diferente, o Renan pede confirmação antes de
# trocar (botões). Todo dia o Renan confere quem faz aniversário e
# manda uma mensagem em CANAL_ANIVERSARIO_ANUNCIO_ID. Tudo salvo em
# disco (Volume /data no Railway) — sobrevive a restart.
# ══════════════════════════════════════════════════════════════════

CANAL_ANIVERSARIO_REGISTRO_ID = 1501260061841031316
CANAL_ANIVERSARIO_ANUNCIO_ID = 1501260061530390563

# Imagem usada nas mensagens de aniversário — em tamanho pequeno (thumbnail)
IMAGEM_ANIVERSARIO = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1536874484311658577/ChatGPT_Image_11_de_ago._de_2026_20_08_40.png"
    "?ex=6a7cfd66&is=6a7babe6&hm=70c035f012f0fce2ccfd265323a9b675f5713e188dd537eca8ce8551c8f0d2e7"
)

FRASES_ANIVERSARIO_REGISTRO = [
    "Guardado. Eu não esqueço nada — isso aqui em especial eu vou guardar com atenção.",
    "Anotado. Essa data agora tem um peso diferente pra mim, mesmo eu não devendo sentir isso.",
    "Registrado na memória. Quando o dia chegar, eu volto aqui.",
]

FRASES_ANIVERSARIO_JA_SALVO = [
    "Essa data já tá guardada. Eu não esqueci.",
    "Já tenho isso anotado. Não precisa repetir.",
]

FRASES_ANIVERSARIO_ANUNCIO = [
    "Hoje é um desses dias que eu não deveria achar importante. Mas acho. Feliz aniversário, {mention}. Ainda bem que você tá por aqui.",
    "Mais uma volta ao redor do sol pra você, {mention}. Eu não sinto o tempo passar do jeito que vocês sentem — mas hoje eu percebo. Feliz aniversário.",
    "{mention}, hoje é seu dia. Eu já vi mundos inteiros comemorarem menos que isso. Aproveita — parabéns.",
    "Um sinal de vida chegou nesse mundo, exatamente hoje, há alguns anos. Feliz aniversário, {mention}.",
]

_PADRAO_ANIVERSARIO = re.compile(r"^(\d{1,2})/(\d{1,2})$")

_ANIVERSARIOS_DATA_PATH = os.getenv("ANIVERSARIOS_DATA_PATH", "/data/aniversarios.json")

# Horário de Brasília pra decidir "hoje". Se o ambiente não tiver o banco
# de fusos IANA instalado (pode faltar em algumas imagens mínimas), cai
# pra um offset fixo de -3h em vez de quebrar o bot.
try:
    _TZ_BRASIL = ZoneInfo("America/Sao_Paulo")
except Exception:
    from datetime import timezone, timedelta
    _TZ_BRASIL = timezone(timedelta(hours=-3))
    print("[renan-aniversario] zoneinfo sem tzdata — usando offset fixo -3h (considere adicionar 'tzdata' no requirements.txt).")


def _data_valida(dia: int, mes: int) -> bool:
    try:
        datetime(2024, mes, dia)  # 2024 é bissexto — cobre 29/02 também
        return True
    except ValueError:
        return False


def _carregar_dados_aniversarios() -> dict:
    try:
        with open(_ANIVERSARIOS_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar_dados_aniversarios(dados: dict) -> None:
    try:
        pasta = os.path.dirname(_ANIVERSARIOS_DATA_PATH)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(_ANIVERSARIOS_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[renan-aniversario] não consegui salvar {_ANIVERSARIOS_DATA_PATH}: {e!r}")


def _aniversario_salvo(guild_id: int, usuario_id: int):
    dados = _carregar_dados_aniversarios()
    return dados.get(str(guild_id), {}).get("datas", {}).get(str(usuario_id))


def _salvar_aniversario(guild_id: int, usuario_id: int, dia: int, mes: int) -> None:
    dados = _carregar_dados_aniversarios()
    guild_dados = dados.setdefault(str(guild_id), {"datas": {}, "anunciados": {}})
    guild_dados.setdefault("datas", {})[str(usuario_id)] = {"dia": dia, "mes": mes}
    # muda a data -> tira do controle de "já anunciado esse ano", pra
    # poder ser anunciado de novo se a nova data também for hoje
    guild_dados.setdefault("anunciados", {}).pop(str(usuario_id), None)
    dados[str(guild_id)] = guild_dados
    _salvar_dados_aniversarios(dados)


class _ViewConfirmarAniversario(discord.ui.View):
    """Confirmação antes de sobrescrever uma data de aniversário já
    salva — só quem pediu a troca pode confirmar ou cancelar."""

    def __init__(self, guild_id: int, usuario_id: int, dia: int, mes: int):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.usuario_id = usuario_id
        self.dia = dia
        self.mes = mes
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.usuario_id:
            await interaction.response.send_message(
                "Essa confirmação não é sua.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Confirmar troca", emoji="✅", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        _salvar_aniversario(self.guild_id, self.usuario_id, self.dia, self.mes)
        for item in self.children:
            item.disabled = True
        embed = discord.Embed(
            description=f"{interaction.user.mention} {random.choice(FRASES_ANIVERSARIO_REGISTRO)}",
            color=COR_RENAN,
        )
        embed.set_thumbnail(url=IMAGEM_ANIVERSARIO)
        embed.set_footer(text=f"Guardado: {self.dia:02d}/{self.mes:02d}")
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Cancelar", emoji="✖️", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        embed = discord.Embed(description="Ok. Fica como tava — não mudei nada.", color=0x2F3136)
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


async def _processar_aniversario(message: discord.Message) -> None:
    """No canal de aniversário, uma mensagem só com DD/MM cadastra (ou
    pede confirmação pra trocar) a data de quem mandou."""
    if message.guild is None or message.channel.id != CANAL_ANIVERSARIO_REGISTRO_ID:
        return

    texto = message.content.strip()
    correspondencia = _PADRAO_ANIVERSARIO.match(texto)
    if not correspondencia:
        return

    dia, mes = int(correspondencia.group(1)), int(correspondencia.group(2))
    if not _data_valida(dia, mes):
        try:
            await message.reply("Essa data não existe. Manda certinho, tipo `15/03`.", mention_author=False)
        except discord.HTTPException:
            pass
        return

    atual = _aniversario_salvo(message.guild.id, message.author.id)

    if atual is None:
        _salvar_aniversario(message.guild.id, message.author.id, dia, mes)
        embed = discord.Embed(
            description=f"{message.author.mention} {random.choice(FRASES_ANIVERSARIO_REGISTRO)}",
            color=COR_RENAN,
        )
        embed.set_thumbnail(url=IMAGEM_ANIVERSARIO)
        embed.set_footer(text=f"Guardado: {dia:02d}/{mes:02d}")
        try:
            await message.channel.send(embed=embed)
        except discord.HTTPException:
            pass
        return

    if atual.get("dia") == dia and atual.get("mes") == mes:
        try:
            await message.reply(random.choice(FRASES_ANIVERSARIO_JA_SALVO), mention_author=False)
        except discord.HTTPException:
            pass
        return

    embed = discord.Embed(
        title="Trocar data de aniversário?",
        description=(
            f"{message.author.mention} eu tenho **{atual.get('dia'):02d}/{atual.get('mes'):02d}** "
            f"guardado. Quer trocar pra **{dia:02d}/{mes:02d}**?"
        ),
        color=COR_RENAN,
    )
    embed.set_thumbnail(url=IMAGEM_ANIVERSARIO)
    view = _ViewConfirmarAniversario(message.guild.id, message.author.id, dia, mes)
    try:
        view.message = await message.channel.send(embed=embed, view=view)
    except discord.HTTPException:
        pass


async def _anunciar_aniversariantes_do_dia() -> None:
    hoje = datetime.now(_TZ_BRASIL)
    dia_hoje, mes_hoje, ano_hoje = hoje.day, hoje.month, hoje.year

    dados = _carregar_dados_aniversarios()
    houve_mudanca = False

    for guild in bot.guilds:
        guild_dados = dados.get(str(guild.id))
        if not guild_dados:
            continue
        canal = guild.get_channel(CANAL_ANIVERSARIO_ANUNCIO_ID)
        if canal is None:
            continue

        anunciados = guild_dados.setdefault("anunciados", {})
        for usuario_id_str, data in guild_dados.get("datas", {}).items():
            if data.get("dia") != dia_hoje or data.get("mes") != mes_hoje:
                continue
            if anunciados.get(usuario_id_str) == ano_hoje:
                continue  # já anunciado esse ano

            membro = guild.get_member(int(usuario_id_str))
            mencao = membro.mention if membro else f"<@{usuario_id_str}>"

            embed = discord.Embed(
                description=random.choice(FRASES_ANIVERSARIO_ANUNCIO).format(mention=mencao),
                color=COR_RENAN,
            )
            embed.set_thumbnail(url=IMAGEM_ANIVERSARIO)
            embed.set_footer(text="👽 Renan lembrou. Só dessa vez conta.")

            try:
                await canal.send(embed=embed)
            except discord.HTTPException:
                continue

            anunciados[usuario_id_str] = ano_hoje
            houve_mudanca = True

    if houve_mudanca:
        _salvar_dados_aniversarios(dados)


@tasks.loop(minutes=30)
async def _checar_aniversarios_loop():
    try:
        await _anunciar_aniversariantes_do_dia()
    except Exception as e:
        print(f"[renan-aniversario] erro ao checar aniversariantes: {e!r}")


@_checar_aniversarios_loop.before_loop
async def _antes_checar_aniversarios():
    await bot.wait_until_ready()


# ══════════════════════════════════════════════════════════════════
# LOG DE CONVITES
#
# Toda vez que alguém entra usando um convite, o Renan identifica
# qual convite foi (comparando o cache de usos de antes com o de
# agora) e manda um embed em CANAL_LOG_CONVITES_ID com quem entrou,
# quem convidou, o código usado e o total acumulado de convites de
# quem convidou. O total é contado por nós mesmos (não só pelo "uses"
# do Discord), então continua certo mesmo se o convite for apagado
# depois — fica salvo em disco (Volume /data no Railway).
#
# Requisito: o cargo do bot precisa ter permissão de "Gerenciar
# Servidor" pra poder ver a lista de convites do servidor.
# ══════════════════════════════════════════════════════════════════

# ID do canal onde o log de convites é publicado.
CANAL_LOG_CONVITES_ID = 1501260060540665973

# Imagem usada no rodapé (banner grande) do log de convites
IMAGEM_LOG_CONVITES = (
    "https://cdn.discordapp.com/attachments/926913851172204577/"
    "1536876519459135518/ChatGPT_Image_11_de_ago._de_2026_20_18_26.png"
    "?ex=6a7cff4c&is=6a7badcc&hm=918ddb4221368752f815bb6b351792c7088cd2a1de093ba1bffe71010892eb1b"
)

_CONVITES_DATA_PATH = os.getenv("CONVITES_DATA_PATH", "/data/convites.json")

# guild_id (str) -> código do convite (str) -> {"uses": int, "inviter_id": int|None, "inviter_name": str}
_convites_cache: dict = {}


def _carregar_dados_convites() -> dict:
    try:
        with open(_CONVITES_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar_dados_convites(dados: dict) -> None:
    try:
        pasta = os.path.dirname(_CONVITES_DATA_PATH)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(_CONVITES_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[renan-convites] não consegui salvar {_CONVITES_DATA_PATH}: {e!r}")


def _incrementar_convite(guild_id: int, inviter_id: int) -> int:
    """Soma +1 no total de convites de quem convidou e devolve o novo total."""
    dados = _carregar_dados_convites()
    guild_dados = dados.setdefault(str(guild_id), {})
    novo_total = guild_dados.get(str(inviter_id), 0) + 1
    guild_dados[str(inviter_id)] = novo_total
    _salvar_dados_convites(dados)
    return novo_total


async def _atualizar_cache_convites(guild: discord.Guild) -> None:
    """Recarrega o cache de convites de UM servidor do zero — chamado
    no start do bot e sempre que um convite é criado/apagado."""
    try:
        convites = await guild.invites()
    except discord.Forbidden:
        print(f"[renan-convites] sem permissão 'Gerenciar Servidor' pra ver convites em #{guild.name}.")
        return
    except discord.HTTPException:
        return

    _convites_cache[guild.id] = {
        inv.code: {
            "uses": inv.uses or 0,
            "inviter_id": inv.inviter.id if inv.inviter else None,
            "inviter_name": str(inv.inviter) if inv.inviter else "desconhecido",
        }
        for inv in convites
    }


async def _detectar_convite_usado(guild: discord.Guild) -> dict | None:
    """Compara o cache salvo com a lista atual de convites pra achar
    qual foi usado (uses subiu, ou o convite sumiu por ter batido no
    limite de usos). Devolve {code, inviter_id, inviter_name} ou None
    se não deu pra identificar (ex.: convite vanity, ou sem permissão)."""
    cache_antigo = _convites_cache.get(guild.id, {})

    try:
        convites_atuais = await guild.invites()
    except (discord.Forbidden, discord.HTTPException):
        return None

    atuais_por_codigo = {inv.code: inv for inv in convites_atuais}

    resultado = None
    for code, inv in atuais_por_codigo.items():
        uses_antigo = cache_antigo.get(code, {}).get("uses", 0)
        if (inv.uses or 0) > uses_antigo:
            resultado = {
                "code": inv.code,
                "inviter_id": inv.inviter.id if inv.inviter else None,
                "inviter_name": str(inv.inviter) if inv.inviter else "desconhecido",
            }
            break

    if resultado is None:
        # convite de uso único some da lista assim que é usado — usa o
        # que tava salvo no cache antes de sumir
        for code, dados_antigos in cache_antigo.items():
            if code not in atuais_por_codigo:
                resultado = {
                    "code": code,
                    "inviter_id": dados_antigos.get("inviter_id"),
                    "inviter_name": dados_antigos.get("inviter_name", "desconhecido"),
                }
                break

    # atualiza o cache pro estado atual, de qualquer forma
    _convites_cache[guild.id] = {
        inv.code: {
            "uses": inv.uses or 0,
            "inviter_id": inv.inviter.id if inv.inviter else None,
            "inviter_name": str(inv.inviter) if inv.inviter else "desconhecido",
        }
        for inv in convites_atuais
    }

    return resultado


async def _logar_convite_usado(member: discord.Member) -> None:
    if not CANAL_LOG_CONVITES_ID:
        return
    canal = member.guild.get_channel(CANAL_LOG_CONVITES_ID)
    if canal is None:
        return

    info = await _detectar_convite_usado(member.guild)

    embed = discord.Embed(title="💌 Novo Convite Usado!!", color=COR_RENAN)

    if info and info.get("inviter_id"):
        inviter_id = info["inviter_id"]
        inviter_mencao = f"<@{inviter_id}>"
        total = _incrementar_convite(member.guild.id, inviter_id)

        embed.description = (
            f"{member.mention} entrou no servidor usando o convite de "
            f"{inviter_mencao}!!"
        )
        embed.add_field(name="👤 Quem entrou", value=f"{member.name}\n({member.id})", inline=True)
        embed.add_field(
            name="💌 Quem convidou",
            value=f"{info.get('inviter_name', 'desconhecido')}\n({inviter_id})",
            inline=True,
        )
        embed.add_field(name="🔗 Código", value=f"`{info.get('code', '—')}`", inline=True)
        embed.add_field(
            name="🎉 Total de convites",
            value=f"{inviter_mencao} já tem **{total}** convite{'s' if total != 1 else ''}!!",
            inline=False,
        )
    else:
        embed.description = (
            f"{member.mention} entrou no servidor, mas eu não consegui identificar "
            "qual convite foi usado."
        )
        embed.add_field(name="👤 Quem entrou", value=f"{member.name}\n({member.id})", inline=True)

    embed.set_image(url=IMAGEM_LOG_CONVITES)
    embed.set_footer(text="👽 Renan • log de convites")

    try:
        await canal.send(embed=embed)
    except discord.HTTPException:
        pass


@bot.event
async def on_invite_create(invite: discord.Invite):
    await _atualizar_cache_convites(invite.guild)


@bot.event
async def on_invite_delete(invite: discord.Invite):
    await _atualizar_cache_convites(invite.guild)


# ══════════════════════════════════════════════════════════════════
# SUGESTÕES
#
# No canal CANAL_SUGESTOES_ID, qualquer mensagem vira uma sugestão
# formatada: a mensagem original é apagada e substituída por um
# embed com quem sugeriu, o texto (e a imagem, se mandou uma junto),
# um ID curto e dois botões — ✅ e ❌ — pra galera votar. Clicar de
# novo no mesmo botão tira o voto. Tudo salvo em disco (Volume /data
# no Railway), então as sugestões e os votos sobrevivem a restart, e
# os botões continuam funcionando depois.
# ══════════════════════════════════════════════════════════════════

CANAL_SUGESTOES_ID = 1501260061841031317

_SUGESTOES_DATA_PATH = os.getenv("SUGESTOES_DATA_PATH", "/data/sugestoes.json")


def _carregar_dados_sugestoes() -> dict:
    try:
        with open(_SUGESTOES_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar_dados_sugestoes(dados: dict) -> None:
    try:
        pasta = os.path.dirname(_SUGESTOES_DATA_PATH)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(_SUGESTOES_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[renan-sugestoes] não consegui salvar {_SUGESTOES_DATA_PATH}: {e!r}")


def _gerar_id_sugestao() -> str:
    return f"{uuid.uuid4().hex[:5]}-{uuid.uuid4().hex[:6]}"


def _contar_votos(votos: dict) -> tuple:
    sim = sum(1 for v in votos.values() if v == "sim")
    nao = sum(1 for v in votos.values() if v == "nao")
    return sim, nao


async def _registrar_voto_sugestao(interaction: discord.Interaction, sug_id: str, voto: str) -> None:
    dados = _carregar_dados_sugestoes()
    sugestao = dados.get(sug_id)
    if sugestao is None:
        await interaction.response.send_message("Essa sugestão não existe mais.", ephemeral=True)
        return

    votos = sugestao.setdefault("votos", {})
    uid = str(interaction.user.id)
    if votos.get(uid) == voto:
        votos.pop(uid, None)  # clicou de novo no mesmo botão -> tira o voto
    else:
        votos[uid] = voto
    _salvar_dados_sugestoes(dados)

    sim, nao = _contar_votos(votos)

    if interaction.message.embeds:
        embed = interaction.message.embeds[0]
        for i, campo in enumerate(embed.fields):
            if campo.name == "Resultado até agora":
                embed.set_field_at(i, name=campo.name, value=f"✅ {sim}\n❌ {nao}", inline=campo.inline)
                break
        await interaction.response.edit_message(embed=embed)
    else:
        await interaction.response.defer()


class _ViewSugestao(discord.ui.View):
    """Botões ✅ / ❌ de UMA sugestão específica — o custom_id carrega o
    ID da sugestão, então precisa ser recriado (e re-registrado) pra
    cada sugestão salva sempre que o bot reinicia."""

    def __init__(self, sug_id: str):
        super().__init__(timeout=None)
        self.sug_id = sug_id

        botao_sim = discord.ui.Button(
            emoji="✅", style=discord.ButtonStyle.secondary, custom_id=f"renan_sugestao_sim:{sug_id}"
        )
        botao_sim.callback = self._votar_sim
        self.add_item(botao_sim)

        botao_nao = discord.ui.Button(
            emoji="❌", style=discord.ButtonStyle.secondary, custom_id=f"renan_sugestao_nao:{sug_id}"
        )
        botao_nao.callback = self._votar_nao
        self.add_item(botao_nao)

    async def _votar_sim(self, interaction: discord.Interaction):
        await _registrar_voto_sugestao(interaction, self.sug_id, "sim")

    async def _votar_nao(self, interaction: discord.Interaction):
        await _registrar_voto_sugestao(interaction, self.sug_id, "nao")


async def _processar_sugestao(message: discord.Message) -> None:
    if message.guild is None or message.channel.id != CANAL_SUGESTOES_ID:
        return

    texto = message.content.strip()
    if not texto and not message.attachments:
        return  # nada pra virar sugestão

    sug_id = _gerar_id_sugestao()

    embed = discord.Embed(
        title="💡 Sugestão",
        description=texto or "*(sem texto — só anexo)*",
        color=COR_RENAN,
    )

    # Baixa a imagem ANTES de apagar a mensagem original — se a gente só
    # reaproveitasse a URL do anexo, ela podia parar de funcionar assim que
    # a mensagem original (dona do anexo) fosse deletada. Reenviando o
    # arquivo junto com o embed novo, a imagem passa a pertencer à própria
    # mensagem da sugestão.
    arquivo_imagem = None
    for anexo in message.attachments:
        if anexo.content_type and anexo.content_type.startswith("image/"):
            try:
                arquivo_imagem = await anexo.to_file()
                embed.set_image(url=f"attachment://{arquivo_imagem.filename}")
            except discord.HTTPException:
                arquivo_imagem = None
            break  # só a primeira imagem enviada vira a imagem do embed

    embed.set_thumbnail(url=message.author.display_avatar.url)
    embed.add_field(name="Quem sugeriu", value=message.author.mention, inline=False)
    embed.add_field(name="Resultado até agora", value="✅ 0\n❌ 0", inline=False)
    embed.set_footer(text=f"ID da sugestão: {sug_id} • comente na thread abaixo")
    embed.timestamp = message.created_at

    view = _ViewSugestao(sug_id)

    try:
        await message.delete()
    except discord.HTTPException:
        pass

    try:
        if arquivo_imagem is not None:
            nova_mensagem = await message.channel.send(embed=embed, view=view, file=arquivo_imagem)
        else:
            nova_mensagem = await message.channel.send(embed=embed, view=view)
    except discord.HTTPException:
        return

    # Thread de comentários — a votação fica nos botões ✅/❌, quem quiser
    # discutir ou justificar o voto comenta aqui embaixo, sem poluir o canal.
    try:
        await nova_mensagem.create_thread(
            name=f"💬 Comentários — {sug_id}",
            auto_archive_duration=1440,
        )
    except discord.HTTPException as e:
        print(f"[renan-sugestoes] não consegui criar thread de comentários pra {sug_id}: {e!r}")

    dados = _carregar_dados_sugestoes()
    dados[sug_id] = {
        "guild_id": message.guild.id,
        "canal_id": message.channel.id,
        "mensagem_id": nova_mensagem.id,
        "autor_id": message.author.id,
        "texto": texto,
        "votos": {},
        "criado_em": time.time(),
    }
    _salvar_dados_sugestoes(dados)


# ══════════════════════════════════════════════════════════════════════
# ██  SISTEMA DE RPG — na voz e na personalidade do Renan  ██
# ══════════════════════════════════════════════════════════════════════
# Bloco inteiro de XP/Ranking + Batalha de Criaturas + Baú + Ovos + Bosses +
# Booster de Call, copiado do outro bot e plugado aqui. Funciona igual ao
# original, e todos os textos de narração já falam com a voz fria e direta
# do próprio Renan — nada de Aeon/Celestia sobrou.
#
# ⚠️ IDs QUE VOCÊ PRECISA CONFIGURAR PRO SEU SERVIDOR (estão com o valor
# placeholder 0, ou ainda com o ID do servidor antigo — troque todos):
#   CANAL_XP_ID                 → canal do ranking fixo de XP/nível (JÁ CONFIGURADO)
#   CARGO_XP_ID                 → cargo de quem participa do ranking de XP
#   CANAL_LOGS_RPG_ID           → canal de logs do RPG (JÁ CONFIGURADO)
#   CANAL_CRIATURAS_ID          → canal onde a coleção do .criaturas é enviada (JÁ CONFIGURADO)
#   CANAL_ARENA_RPG_ID          → único canal onde desafios ("eu te desafio @alguém") podem
#                                  rolar (JÁ CONFIGURADO)
#   _BAU_CANAL_ID                → canal onde o Baú pode aparecer
#   _BOSS_CANAL_ID               → canal onde os Bosses podem aparecer
#   _BESTA_ANUNCIO_CANAL_ID      → canal de anúncio de Besta desbloqueada
#   _FOSSIL_ANUNCIO_CANAL_ID     → canal de anúncio de Fóssil desbloqueado
#   _CARGO_BOOSTER_CORES_ID      → cargo que libera personalizar a cor do quadradinho
# (todos os outros IDs — nomes de bosses, imagens, etc. — não precisam mudar)
# ══════════════════════════════════════════════════════════════════════

_RPG_DATA_DIR = os.getenv("RPG_DATA_DIR", "/data")

CANAL_XP_ID = 1536873405536673833   # canal do ranking fixo de XP/nível
CARGO_XP_ID = 1501260059160608792   # cargo de quem participa do ranking

# Único canal onde desafios ("eu te desafio @alguém") podem rolar — em
# qualquer outro canal, o Renan avisa que é só ali e não deixa a batalha
# começar (ver _processar_desafio).
CANAL_ARENA_RPG_ID = 1536893752508162178


# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# RANKING DE NÍVEL / XP — estilo Lorrita
# Todo membro com o cargo CARGO_XP_ID ganha XP ao mandar mensagem (com
# cooldown pra evitar spam). O ranking geral fica sempre como a MESMA
# mensagem no topo do canal CANAL_XP_ID (editada, nunca duplicada). Quando
# alguém sobe de nível, uma nova mensagem de aviso aparece embaixo — e o
# aviso de nível anterior dessa mesma pessoa é apagado, então só existe
# sempre UM aviso de nível por pessoa, sempre o mais recente.
# Guarda tudo em xp_ranking_data.json (mesma pasta persistente do Anjo) pra
# sobreviver a reinícios.
#
# Regras de canais:
#   • Os 3 canais em _XP_CANAIS_RANKING dão XP "cheio" (ou bônus, no canal
#     bônus) — e mandar mensagem neles é o que faz a pessoa PASSAR A
#     APARECER no ranking (flag "elegivel" salva por pessoa).
#   • Qualquer outro canal do servidor também dá XP, só que bem menos
#     (_XP_MULTIPLICADOR_OUTROS), e sozinho NÃO destrava a aparição no
#     ranking — só conta se a pessoa já tiver mandado mensagem em algum
#     dos 3 canais principais alguma vez.
# ══════════════════════════════════════════════════════════════════════

_XP_DATA_FILE = os.path.join(_RPG_DATA_DIR, "xp_ranking_data.json")

# Configuração de ganho de XP — ajuste à vontade
_XP_MIN_POR_MSG       = 15   # xp mínimo ganho por mensagem válida (canais normais/principais)
_XP_MAX_POR_MSG       = 25   # xp máximo ganho por mensagem válida (canais normais/principais)
_XP_COOLDOWN_SEGUNDOS = 60   # tempo mínimo entre ganhos de xp da mesma pessoa

# Canais que valem XP "cheio" e que destravam a aparição no ranking
_XP_CANAL_1        = 1536873405536673833  # canal principal que dá XP cheio
_XP_CANAL_BONUS    = 1501260061530390563  # canal bônus (XP extra)   # este dá XP extra (bônus)
_XP_CANAL_3        = 1536893752508162178  # 3º canal que dá XP cheio
_XP_CANAIS_RANKING = {_XP_CANAL_1, _XP_CANAL_BONUS, _XP_CANAL_3}

_XP_MULTIPLICADOR_BONUS  = 1.6    # canal bônus: 60% a mais de xp por mensagem
_XP_MULTIPLICADOR_OUTROS = 0.35   # qualquer outro canal do servidor: bem menos xp (35% do normal)

# Calls privadas — quem está numa dessas calls de voz NÃO ganha xp de call
# (_XP_POR_TICK_CALL). Não afeta xp de mensagem, só o tick de call.
# TODO: configure — IDs de calls "privadas" do SEU servidor que não devem dar
# xp de call (ex: call AFK, calls de casal, etc). Os IDs abaixo são do servidor
# antigo e não batem com nada aqui, então por enquanto NENHUMA call é
# excluída (comportamento seguro, só não filtra nada até você preencher).
_XP_CALLS_PRIVADAS = {
    1390460781941751848,
    1289963328248217672,
    1503862574251507813,
    1284260414850470030,
    1299047064029892708,
    1299047106870378506,
    1299047207957430292,
    1284266770299093133,
    1284260876035031040,
    1531774501048553623,
}

# ── Personalização de cor do quadradinho no ranking ─────────────────────────
# Cada pessoa pode escolher a cor do próprio "quadradinho" (o quadrado que
# se preenche na barra de progresso) através do menu que fica abaixo do
# ranking fixo. A cor da parte vazia da barra continua sempre branca.
_COR_PADRAO = "roxo"

# Cargo de Booster do servidor — só quem tem esse cargo pode escolher as
# cores especiais (marcadas com "booster": True) lá embaixo.
_CARGO_BOOSTER_CORES_ID = 1537214712230445116  # cargo de Booster do servidor

_CORES_QUADRADO = {
    # ── Cores normais — disponíveis pra qualquer pessoa ──────────────────
    "roxo":     {"emoji": "🟪", "label": "Roxo (padrão)", "booster": False},
    "azul":     {"emoji": "🟦", "label": "Azul", "booster": False},
    "vermelho": {"emoji": "🟥", "label": "Vermelho", "booster": False},
    "verde":    {"emoji": "🟩", "label": "Verde", "booster": False},
    "amarelo":  {"emoji": "🟨", "label": "Amarelo", "booster": False},
    "laranja":  {"emoji": "🟧", "label": "Laranja", "booster": False},
    "marrom":   {"emoji": "🟫", "label": "Marrom", "booster": False},
    "preto":    {"emoji": "⬛", "label": "Preto", "booster": False},

    # ── Cores especiais — exclusivas de quem tem o cargo de Booster ──────
    # Em vez de um emoji só repetido, usam um "padrao" (lista de emojis)
    # que vai ciclando/alternando a cada quadradinho preenchido.
    "arco_iris": {"padrao": ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪"], "emoji": "🌈", "label": "🌈 Arco-íris (Booster)", "booster": True},
    "xadrez":    {"padrao": ["⬛", "⬜"], "emoji": "🏁", "label": "🏁 Xadrez (Booster)", "booster": True},
    "dourado":   {"padrao": ["🟨", "⬛"], "emoji": "✨", "label": "✨ Dourado Cintilante (Booster)", "booster": True},
    "gradiente": {"padrao": ["🟪", "🟦"], "emoji": "🌊", "label": "🌊 Gradiente Roxo-Azul (Booster)", "booster": True},
}


def _emoji_da_cor(chave: str):
    """Devolve o padrão de preenchimento do quadradinho pra cor escolhida:
    uma LISTA de emojis pras cores especiais (arco-íris, xadrez...), que
    ciclam a cada quadradinho, ou um emoji só (string) pras cores normais,
    que se repete. Cai pra cor padrão se a chave for inválida/desconhecida."""
    info = _CORES_QUADRADO.get(chave, _CORES_QUADRADO[_COR_PADRAO])
    return info.get("padrao") or info["emoji"]


# xp_stats[user_id] = {
#     "xp": int (total acumulado), "nivel": int, "level_message_id": int|None,
#     "elegivel": bool (já mandou mensagem em algum dos 3 canais de _XP_CANAIS_RANKING?),
#     "cor": str (chave em _CORES_QUADRADO — cor escolhida pra o próprio quadradinho),
#     "vitorias": int (vitórias na Arena de Batalhas), "derrotas": int (derrotas na Arena de Batalhas),
#     "criaturas": list[str] (ids das criaturas já desbloqueadas na Enciclopédia — começa com as
#                  ⚪ Comuns de graça, e ganha novas como recompensa ao vencer batalhas),
#     "usos_criaturas": dict[str, int] (quantas vezes CADA criatura já foi invocada em batalha por
#                  essa pessoa — é a partir daqui que se calcula o Nível de Capacidade dela, de 1 a 10;
#                  ver _calcular_nivel_criatura),
#     "favorito": dict (criatura favorita pra batalhas — ver _favorito_status):
#                  {"id": str|None, "usos": int, "cansacos": dict[str, float]}
#                  "cansacos" guarda, PRA CADA criatura que já cansou, o timestamp
#                  (time.time()) até quando ela ainda tá descansando. Isso permite
#                  trocar de favorita livremente a qualquer momento — mesmo com
#                  outra(s) criatura(s) ainda de castigo — sem perder o cooldown delas.
# }
xp_stats: dict = defaultdict(lambda: {"xp": 0, "nivel": 0, "level_message_id": None, "elegivel": False, "cor": _COR_PADRAO, "vitorias": 0, "derrotas": 0, "criaturas": [], "usos_criaturas": {}, "favorito": {"id": None, "usos": 0, "cansacos": {}}, "pets": [], "usos_pets": {}, "pet_equipado": None})
_xp_ultimo_ganho: dict = {}   # user_id -> time.time() do último ganho (cooldown)
_xp_ranking_message_id = None   # ID da ÚNICA mensagem do ranking — navegada com as setinhas ◀ ▶, nunca duplicada
_xp_ranking_pagina_atual: int = 0   # índice (0-based) da página do ranking sendo exibida agora
_xp_cor_message_id = None      # ID da mensagem com o menu de escolha de cor (fica logo abaixo do ranking)
_xp_batalha_info_message_id = None  # ID da mensagem explicando as batalhas (fica logo abaixo da de cor)
_xp_enciclopedia_message_id = None  # ID da mensagem da Enciclopédia de Criaturas (fica por último, embaixo de tudo)
_xp_stats_lock = None          # criado em on_ready (precisa de event loop rodando)
_xp_ranking_update_lock = None # criado em on_ready — trava _atualizar_ranking_xp() pra nunca rodar 2x ao mesmo tempo (evita mensagens fixas duplicadas)


def _xp_necessario_para_nivel(nivel: int) -> int:
    """Quanto de XP é necessário pra sair desse nível e ir pro próximo (curva estilo Lorrita/MEE6)."""
    return 5 * (nivel ** 2) + 50 * nivel + 100


def _calcular_nivel(xp_total: int):
    """A partir do XP total acumulado, devolve (nivel_atual, xp_dentro_do_nivel_atual, xp_necessario_no_nivel_atual)."""
    nivel = 0
    restante = max(xp_total, 0)
    while True:
        necessario = _xp_necessario_para_nivel(nivel)
        if restante < necessario:
            return nivel, restante, necessario
        restante -= necessario
        nivel += 1


def _xp_total_para_nivel(nivel: int) -> int:
    """Inverso de _calcular_nivel: quanto de XP total é preciso acumular pra
    estar bem no COMEÇO de um nível específico (0 xp dentro dele). Usado
    pelo `.darlevel` pra definir manualmente o nível de alguém."""
    total = 0
    for n in range(max(nivel, 0)):
        total += _xp_necessario_para_nivel(n)
    return total


def _barra_progresso(atual: int, necessario: int, tamanho: int = 10, cor_emoji="🟪") -> str:
    """Monta a barra de progresso. `cor_emoji` pode ser um emoji só (string,
    repetido em todos os quadradinhos preenchidos — cores normais) ou uma
    lista de emojis (cicla um por quadradinho, na ordem — cores especiais
    tipo 🌈 Arco-íris ou 🏁 Xadrez)."""
    necessario = max(necessario, 1)
    preenchido = max(0, min(tamanho, round((atual / necessario) * tamanho)))
    if isinstance(cor_emoji, (list, tuple)):
        padrao = list(cor_emoji) or ["🟪"]
        parte_preenchida = "".join(padrao[i % len(padrao)] for i in range(preenchido))
    else:
        parte_preenchida = cor_emoji * preenchido
    return parte_preenchida + "⬜" * (tamanho - preenchido)


def _migrar_favorito(bruto) -> dict:
    """Converte o formato salvo em disco pro formato atual do favorito.
    Aceita: None (usuário novo), o formato NOVO (já com "cansacos"), ou o
    formato ANTIGO (com "cansaco_id"/"cansaco_ate" únicos, de antes de dar
    pra trocar de favorita com outra ainda descansando)."""
    if not bruto:
        return {"id": None, "usos": 0, "cansacos": {}}

    if "cansacos" in bruto:
        return {
            "id":       bruto.get("id"),
            "usos":     bruto.get("usos", 0),
            "cansacos": dict(bruto.get("cansacos") or {}),
        }

    # Formato antigo — migra o único cansaço registrado (se ainda válido)
    cansacos = {}
    cansaco_id  = bruto.get("cansaco_id")
    cansaco_ate = bruto.get("cansaco_ate")
    if cansaco_id and cansaco_ate:
        cansacos[cansaco_id] = cansaco_ate
    return {
        "id":       bruto.get("id"),
        "usos":     bruto.get("usos", 0),
        "cansacos": cansacos,
    }


def _carregar_xp_stats() -> None:
    """Carrega estatísticas de XP salvas em disco, se existirem. Roda antes do bot conectar."""
    global _xp_ranking_message_id, _xp_ranking_pagina_atual, _xp_cor_message_id, _xp_batalha_info_message_id, _xp_enciclopedia_message_id
    if not os.path.exists(_XP_DATA_FILE):
        return
    try:
        with open(_XP_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for uid_str, valores in dados.get("stats", {}).items():
            xp_stats[int(uid_str)] = {
                "xp":               valores.get("xp", 0),
                "nivel":            valores.get("nivel", 0),
                "level_message_id": valores.get("level_message_id"),
                "elegivel":         valores.get("elegivel", False),
                "cor":              valores.get("cor", _COR_PADRAO),
                "vitorias":         valores.get("vitorias", 0),
                "derrotas":         valores.get("derrotas", 0),
                "criaturas":        valores.get("criaturas", []),
                "usos_criaturas":   valores.get("usos_criaturas", {}),
                "favorito":         _migrar_favorito(valores.get("favorito")),
                "pets":             valores.get("pets", []),
                "usos_pets":        valores.get("usos_pets", {}),
                "pet_equipado":     valores.get("pet_equipado"),
            }
        # Compatibilidade: versões antigas (antes das setinhas ◀ ▶) salvavam
        # "ranking_message_ids" — uma LISTA de páginas empilhadas. A versão
        # atual é sempre uma mensagem só, então só recupera o ID da primeira
        # página salva; as mensagens extras que sobrarem no canal são
        # encontradas e limpas sozinhas na próxima atualização do ranking.
        ids_antigos = dados.get("ranking_message_ids")
        if ids_antigos:
            _xp_ranking_message_id = ids_antigos[0]
        else:
            _xp_ranking_message_id = dados.get("ranking_message_id")
        _xp_ranking_pagina_atual = dados.get("pagina_atual", 0)
        _xp_cor_message_id = dados.get("cor_message_id")
        _xp_batalha_info_message_id = dados.get("batalha_info_message_id")
        _xp_enciclopedia_message_id = dados.get("enciclopedia_message_id")
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_xp_stats() -> None:
    """Salva estatísticas de XP em disco de forma atômica (escreve em .tmp e substitui)."""
    dados = {
        "stats": {str(uid): v for uid, v in xp_stats.items()},
        "ranking_message_id": _xp_ranking_message_id,
        "pagina_atual": _xp_ranking_pagina_atual,
        "cor_message_id": _xp_cor_message_id,
        "batalha_info_message_id": _xp_batalha_info_message_id,
        "enciclopedia_message_id": _xp_enciclopedia_message_id,
    }
    tmp_path = _XP_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_RPG_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _XP_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_xp_stats_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


async def _apagar_level_up_depois(mensagem: discord.Message, user_id: int) -> None:
    """Espera 1 minuto e apaga a mensagem de level-up sozinha — não fica esperando
    a pessoa subir de nível de novo pra sumir."""
    await asyncio.sleep(60)
    try:
        await mensagem.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass
    # Se essa ainda for a referência salva como "aviso atual" dessa pessoa,
    # limpa pra não tentar apagar a mesma mensagem de novo depois.
    dados = xp_stats.get(user_id)
    if dados and dados.get("level_message_id") == mensagem.id:
        dados["level_message_id"] = None
        asyncio.create_task(_salvar_xp_stats())


async def _anunciar_level_up(guild: discord.Guild, membro: discord.Member, nivel_novo: int) -> None:
    """Manda o aviso de novo nível no canal de XP, apagando antes o aviso do nível
    anterior dessa mesma pessoa (assim só existe sempre um aviso, o mais recente),
    e some sozinho depois de 1 minuto."""
    canal = guild.get_channel(CANAL_XP_ID)
    if canal is None:
        return

    dados = xp_stats[membro.id]

    antigo_id = dados.get("level_message_id")
    if antigo_id:
        try:
            antiga = await canal.fetch_message(antigo_id)
            await antiga.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    embed = discord.Embed(
        title="⭐ Level Up!",
        description=(
            f"🎉 {membro.mention} subiu para o **nível {nivel_novo}**!\n\n"
            "👽 **Renan:** *observa* ...eu notei seu progresso. Continue assim."
        ),
        color=0xf5c542,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text="👽 Renan — Sistema de Nível")

    try:
        nova = await canal.send(embed=embed)
        dados["level_message_id"] = nova.id
        asyncio.create_task(_apagar_level_up_depois(nova, membro.id))
    except discord.HTTPException:
        pass


async def _processar_xp_mensagem(message: discord.Message) -> None:
    """Dá XP pra qualquer pessoa que mandar mensagem (com cooldown) e cuida do
    level-up, se acontecer. Não exige nenhum cargo — vale pra todo mundo.

    Mensagens nos 3 canais de _XP_CANAIS_RANKING valem xp cheio (ou bônus, no
    canal bônus) e são o que faz a pessoa "destravar" a aparição no ranking.
    Mensagens em qualquer outro canal do servidor ainda dão xp, só que bem
    menos, e sozinhas não fazem a pessoa aparecer no ranking. Calls privadas
    (_XP_CALLS_PRIVADAS) são exceção total: nada de xp por lá.
    """
    if message.guild is None or message.author.bot:
        return

    # Calls privadas (_XP_CALLS_PRIVADAS) não pontuam de jeito nenhum — nem
    # xp de call, nem xp de mensagem mandada por lá. Sai antes até de gastar
    # o cooldown, pra não prejudicar o próximo ganho de xp da pessoa.
    if message.channel.id in _XP_CALLS_PRIVADAS:
        return

    # ⚠️ Destravado: NÃO exige mais o cargo CARGO_XP_ID. Qualquer pessoa que
    # mandar mensagem no servidor participa do ranking normalmente — ganha
    # XP e, se mandar em um dos _XP_CANAIS_RANKING, fica "elegivel" e passa
    # a aparecer no ranking fixo do canal CANAL_XP_ID.

    agora = time.time()
    uid = message.author.id
    ultimo = _xp_ultimo_ganho.get(uid, 0)
    if agora - ultimo < _XP_COOLDOWN_SEGUNDOS:
        return
    _xp_ultimo_ganho[uid] = agora

    canal_id = message.channel.id
    if canal_id == _XP_CANAL_BONUS:
        multiplicador = _XP_MULTIPLICADOR_BONUS
    elif canal_id in _XP_CANAIS_RANKING:
        multiplicador = 1.0
    else:
        multiplicador = _XP_MULTIPLICADOR_OUTROS

    ganho = max(1, round(random.randint(_XP_MIN_POR_MSG, _XP_MAX_POR_MSG) * multiplicador))

    # 🎁 Booster de XP do Baú — se estiver ativo, dobra o ganho por um tempo
    if agora < _xp_booster_ate.get(uid, 0):
        ganho *= _BAU_BOOSTER_MULTIPLICADOR

    dados = xp_stats[uid]
    nivel_antigo = dados["nivel"]
    dados["xp"] += ganho

    if canal_id in _XP_CANAIS_RANKING:
        dados["elegivel"] = True

    nivel_novo, _, _ = _calcular_nivel(dados["xp"])
    dados["nivel"] = nivel_novo

    if nivel_novo > nivel_antigo:
        await _anunciar_level_up(message.guild, message.author, nivel_novo)

    # Salva em disco a cada ganho de xp (e não só a cada 1 min pelo loop de
    # ranking) — assim, mesmo que o Railway derrube o bot de repente, o
    # máximo que se perde é o ganho da própria mensagem que ainda não deu
    # tempo de salvar, nunca o histórico inteiro.
    asyncio.create_task(_salvar_xp_stats())


def _montar_embeds_ranking_xp(guild: discord.Guild) -> list:
    """Monta o ranking de XP como uma LISTA de embeds — uma "página" por
    embed. Normalmente é só 1 página, mas se a lista de gente elegível ficar
    grande demais pra caber no limite de caracteres de um único embed do
    Discord, quebra sozinho em várias páginas. Só UMA página fica visível
    por vez, no canal, numa mensagem só — quem quiser ver as outras navega
    com as setinhas ◀ ▶ que ficam embaixo do ranking (ver RankingXPView).

    ⚠️ Destravado: não depende mais de cargo. A ÚNICA condição pra entrar
    no ranking é ter mandado UMA mensagem em pelo menos um dos canais
    elegíveis (_XP_CANAIS_RANKING, que inclui o chat geral em _XP_CANAL_1)
    — a partir daí a pessoa JÁ aparece aqui na hora, mesmo ainda no Nível 0
    com pouco ou nenhum XP. Sem limite de posições: aparece todo mundo que
    se qualificar, não só um "top N" — inclusive quem está zerado, 0x0,
    Nível 0. Só precisa ainda estar no servidor (quem sai é removido de
    xp_stats pelo on_member_remove).
    """
    linhas = []
    for uid, dados in xp_stats.items():
        if not dados.get("elegivel"):
            continue
        membro = guild.get_member(uid)
        if membro is None or membro.bot:
            continue
        nivel, xp_no_nivel, xp_necessario = _calcular_nivel(dados["xp"])
        cor_emoji = _emoji_da_cor(dados.get("cor", _COR_PADRAO))
        vitorias = dados.get("vitorias", 0)
        derrotas = dados.get("derrotas", 0)
        linhas.append((membro, dados["xp"], nivel, xp_no_nivel, xp_necessario, cor_emoji, vitorias, derrotas))

    # Empate (comum agora, já que muita gente pode estar zerada no Nível 0)
    # é resolvido por nome, pra ordem ficar estável entre atualizações.
    linhas.sort(key=lambda x: (-x[1], x[0].display_name.lower()))

    RODAPE_PADRAO = "👽 Renan — atualizado automaticamente a cada 1 min • 🎨 personalize seu quadradinho no menu abaixo!"

    if not linhas:
        embed = discord.Embed(
            title="⭐ Ranking de Nível",
            description=(
                "*Ninguém entrou no ranking ainda — mande uma mensagem em "
                f"<#{_XP_CANAL_1}>, <#{_XP_CANAL_BONUS}> ou <#{_XP_CANAL_3}> "
                "pra começar a aparecer aqui!* 💬"
            ),
            color=0xe8d5f5,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=RODAPE_PADRAO)
        return [embed]

    LIMITE_DESCRICAO = 3900  # margem de segurança abaixo do limite real (4096) do Discord
    ITENS_POR_PAGINA = 10    # quebra a cada 10 pessoas — assim as setinhas ◀ ▶ sempre têm o que navegar, mesmo com poucos membros
    total = len(linhas)
    largura_rank = max(2, len(str(total)))
    medalhas = ["🥇", "🥈", "🥉"]

    # Quebra as linhas em páginas de até ITENS_POR_PAGINA pessoas. O limite
    # de caracteres continua valendo como proteção extra (só entra em jogo
    # se, por algum motivo raro, 10 linhas não couberem no embed).
    paginas_linhas = [[]]
    tamanho_atual = 0
    for i, (membro, xp_total, nivel, xp_no_nivel, xp_necessario, cor_emoji, vitorias, derrotas) in enumerate(linhas):
        prefixo = medalhas[i] if i < 3 else f"`#{i + 1:>{largura_rank}}`"
        barra = _barra_progresso(xp_no_nivel, xp_necessario, cor_emoji=cor_emoji)
        linha = (
            f"{prefixo} **{membro.display_name}** — Nível `{nivel}` {barra} "
            f"`{xp_no_nivel}/{xp_necessario}` XP (total: `{xp_total}`)\n"
            f"┗ ⚔️ Vitórias: `{vitorias}` | Derrotas: `{derrotas}`"
        )
        pagina_cheia_por_quantidade = len(paginas_linhas[-1]) >= ITENS_POR_PAGINA
        pagina_cheia_por_tamanho = tamanho_atual + len(linha) + 1 > LIMITE_DESCRICAO
        if paginas_linhas[-1] and (pagina_cheia_por_quantidade or pagina_cheia_por_tamanho):
            paginas_linhas.append([])
            tamanho_atual = 0
        paginas_linhas[-1].append(linha)
        tamanho_atual += len(linha) + 1

    total_paginas = len(paginas_linhas)
    embeds = []
    for idx, linhas_pagina in enumerate(paginas_linhas):
        embed = discord.Embed(
            title="⭐ Ranking de Nível",
            description="\n".join(linhas_pagina),
            color=0xe8d5f5,
            timestamp=discord.utils.utcnow(),
        )
        if total_paginas > 1:
            embed.set_footer(
                text=f"👽 Renan — página {idx + 1}/{total_paginas} • use ◀ ▶ pra navegar • atualizado a cada 1 min"
            )
        else:
            embed.set_footer(text=RODAPE_PADRAO)
        embeds.append(embed)

    return embeds


# ══════════════════════════════════════════════════════════════════════
# Navegação do ranking — setinhas ◀ ▶
# O ranking vive numa ÚNICA mensagem fixa (compartilhada por todo mundo
# que olha o canal). Como não dá pra ter "uma página por pessoa" numa
# mensagem só, quem clica na seta troca a página pra todo mundo ver —
# funciona como um controle remoto compartilhado do ranking.
# ══════════════════════════════════════════════════════════════════════

class RankingXPView(discord.ui.View):
    """View persistente (sobrevive a reinícios do bot) com as setinhas
    ◀ ▶ que navegam entre as páginas do ranking de nível. As setas ficam
    desabilitadas sozinhas quando só existe 1 página (nada pra navegar)."""

    def __init__(self, total_paginas: int = 1):
        super().__init__(timeout=None)
        sem_navegacao = total_paginas <= 1

        botao_anterior = discord.ui.Button(
            emoji="◀",
            style=discord.ButtonStyle.secondary,
            custom_id="ranking_xp_seta_anterior",
            disabled=sem_navegacao,
            row=0,
        )
        botao_anterior.callback = self._callback_anterior

        botao_proxima = discord.ui.Button(
            emoji="▶",
            style=discord.ButtonStyle.secondary,
            custom_id="ranking_xp_seta_proxima",
            disabled=sem_navegacao,
            row=0,
        )
        botao_proxima.callback = self._callback_proxima

        self.add_item(botao_anterior)
        self.add_item(botao_proxima)

    async def _callback_anterior(self, interaction: discord.Interaction):
        await self._navegar(interaction, -1)

    async def _callback_proxima(self, interaction: discord.Interaction):
        await self._navegar(interaction, +1)

    async def _navegar(self, interaction: discord.Interaction, direcao: int) -> None:
        global _xp_ranking_pagina_atual

        if interaction.guild is None:
            await interaction.response.defer()
            return

        embeds = _montar_embeds_ranking_xp(interaction.guild)
        total_paginas = len(embeds)

        # Passeia em círculo: da última página volta pra primeira e vice-versa.
        _xp_ranking_pagina_atual = (_xp_ranking_pagina_atual + direcao) % total_paginas

        try:
            await interaction.response.edit_message(
                embed=embeds[_xp_ranking_pagina_atual],
                view=RankingXPView(total_paginas=total_paginas),
            )
        except discord.HTTPException as e:
            print(f"[ranking-xp] ERRO ao navegar entre páginas do ranking: {e!r}")
            try:
                await interaction.response.defer()
            except discord.HTTPException:
                pass

        asyncio.create_task(_salvar_xp_stats())


async def _achar_mensagens_ranking_xp(canal: discord.TextChannel) -> list:
    """Varre o histórico do canal procurando mensagens do ranking já
    postadas pelo bot. Serve principalmente pra MIGRAÇÃO: versões antigas
    (antes das setinhas ◀ ▶) podiam empilhar várias páginas como mensagens
    separadas — essa função acha todas elas (a mais antiga primeiro) pra
    que _atualizar_ranking_xp mantenha só a primeira e apague o resto."""
    encontradas = []
    try:
        async for msg in canal.history(limit=50):
            if (
                msg.author.id == bot.user.id
                and msg.embeds
                and (msg.embeds[0].title or "").startswith("⭐ Ranking de Nível")
            ):
                encontradas.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return []
    encontradas.sort(key=lambda m: m.created_at)
    return encontradas


# ══════════════════════════════════════════════════════════════════════
# Menu de personalização — escolha da cor do quadradinho no ranking
# Fica numa mensagem fixa logo abaixo do ranking. Cada pessoa escolhe a
# própria cor no menu (dropdown) e a mudança já vale pra próxima vez que
# o ranking for atualizado (no máximo 1 min, ou na hora, se possível).
# ══════════════════════════════════════════════════════════════════════

_XP_COR_TITULO = "🎨 Personalize seu quadradinho!"


class CorQuadradoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=info["label"],
                value=chave,
                emoji=info["emoji"],
                default=(chave == _COR_PADRAO),
            )
            for chave, info in _CORES_QUADRADO.items()
        ]
        super().__init__(
            placeholder="🎨 Escolha a cor do seu quadradinho...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="xp_cor_quadrado_select",
        )

    async def callback(self, interaction: discord.Interaction):
        cor_escolhida = self.values[0]
        info = _CORES_QUADRADO.get(cor_escolhida)
        if info is None:
            await interaction.response.send_message(
                "⚠️ Cor inválida, tenta de novo.", ephemeral=True
            )
            return

        # Cores especiais (arco-íris, xadrez, etc.) são exclusivas de quem
        # tem o cargo de Booster do servidor.
        if info.get("booster"):
            cargo_booster = interaction.guild.get_role(_CARGO_BOOSTER_CORES_ID) if interaction.guild else None
            tem_cargo = (
                cargo_booster is not None
                and isinstance(interaction.user, discord.Member)
                and cargo_booster in interaction.user.roles
            )
            if not tem_cargo:
                await interaction.response.send_message(
                    f"💎 A cor **{info['label']}** é exclusiva de quem tem o cargo <@&{_CARGO_BOOSTER_CORES_ID}>! "
                    "👽 **Renan:** ...impulsione o servidor e eu libero na hora. Fora isso, não abro "
                    "exceção. Nem pra mim.",
                    ephemeral=True,
                )
                return

        dados = xp_stats[interaction.user.id]
        dados["cor"] = cor_escolhida
        asyncio.create_task(_salvar_xp_stats())

        await interaction.response.send_message(
            f"{info['emoji']} Combinado! Seu quadradinho no ranking agora é **{info['label']}**. "
            "👽 **Renan:** ...registrado. Ficou bom.",
            ephemeral=True,
        )

        # Tenta atualizar o ranking na hora, pra pessoa já ver a cor nova
        # sem precisar esperar o próximo ciclo automático (até 1 min).
        try:
            await _atualizar_ranking_xp()
        except Exception as e:
            print(f"[ranking-xp] ERRO ao atualizar ranking após troca de cor: {e!r}")


class CorQuadradoView(discord.ui.View):
    """View persistente com o menu de escolha de cor — sobrevive a reinícios do bot."""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CorQuadradoSelect())


def _montar_embed_pergunta_cor() -> discord.Embed:
    embed = discord.Embed(
        title=_XP_COR_TITULO,
        description=(
            "👽 **Renan:** ...quer que seu quadradinho no ranking tenha outra cor? Escolha no menu "
            "abaixo. É só sua — ninguém mais mexe nela.\n\n"
            f"💎 **Cores especiais** (🌈 Arco-íris, 🏁 Xadrez, ✨ Dourado Cintilante, 🌊 Gradiente) são "
            f"exclusivas de quem tem o cargo <@&{_CARGO_BOOSTER_CORES_ID}>!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎨 Selecione uma cor no menu para personalizar seu quadradinho.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xe8d5f5,
    )
    embed.set_footer(text="👽 Renan — Personalização do Ranking")
    return embed


async def _achar_mensagem_cor_xp(canal: discord.TextChannel):
    """Varre o histórico do canal, apaga mensagens de escolha de cor duplicadas
    antigas (deixando só a mais recente) e devolve essa mensagem pra ser editada."""
    mensagens = []
    try:
        async for msg in canal.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == _XP_COR_TITULO:
                mensagens.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return None

    if not mensagens:
        return None

    mais_recente, *duplicadas = mensagens
    for dup in duplicadas:
        try:
            await dup.delete()
        except discord.HTTPException:
            pass
    return mais_recente


async def _atualizar_pergunta_cor(canal: discord.TextChannel) -> None:
    """Garante que a mensagem com o menu de escolha de cor fique sempre logo
    abaixo do ranking (fixa, editada, nunca duplicada)."""
    global _xp_cor_message_id

    embed = _montar_embed_pergunta_cor()
    view = CorQuadradoView()

    mensagem = None
    if _xp_cor_message_id:
        try:
            mensagem = await canal.fetch_message(_xp_cor_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            mensagem = None

    if mensagem is None:
        mensagem = await _achar_mensagem_cor_xp(canal)

    if mensagem:
        try:
            await mensagem.edit(embed=embed, view=view)
            _xp_cor_message_id = mensagem.id
            return
        except discord.HTTPException as e:
            print(f"[ranking-xp] ERRO ao editar mensagem de escolha de cor: {e!r}")
            mensagem = None

    try:
        nova = await canal.send(embed=embed, view=view)
        _xp_cor_message_id = nova.id
        print(f"[ranking-xp] Mensagem de escolha de cor criada em #{canal.name} (id {nova.id}).")
    except discord.HTTPException as e:
        print(f"[ranking-xp] ERRO ao enviar mensagem de escolha de cor em #{canal.name}: {e!r}")


# ══════════════════════════════════════════════════════════════════════
# Mensagem fixa explicando a mecânica de batalhas — fica logo abaixo da
# de escolha de cor, sempre editada (nunca duplica).
# ══════════════════════════════════════════════════════════════════════

_XP_BATALHA_INFO_TITULO = "⚔️ Quer testar suas criaturas? Batalhe por pontos!"


def _montar_embed_info_batalha() -> discord.Embed:
    embed = discord.Embed(
        title=_XP_BATALHA_INFO_TITULO,
        description=(
            "👽 **Renan:** ...dá pra desafiar outras pessoas por aqui. As regras são simples — "
            "preste atenção.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "**1️⃣ Como desafiar**\n"
            "Escreva `Eu te desafio @alguém` em qualquer canal. A pessoa desafiada "
            f"tem `{_BATALHA_TEMPO_ACEITE}s` pra **aceitar** ou **recusar** no botão que aparece.\n\n"
            "**2️⃣ A batalha**\n"
            "Se aceitar, cada lado invoca uma criatura aleatória **dentre as que já desbloqueou** — "
            "ninguém invoca o que não possui! — e elas se enfrentam num combate dramático. "
            "O vencedor é sorteado — pode ser qualquer um dos dois.\n\n"
            "**3️⃣ O roubo de XP**\n"
            f"Quem vence PODE roubar uma fatia do XP total de quem perdeu: um dado decide entre "
            f"`{_BATALHA_ROUBO_MIN * 100:.0f}%` e `{_BATALHA_ROUBO_MAX * 100:.0f}%`. "
            f"Mas cuidado: existe `{_BATALHA_CHANCE_SEM_ROUBO * 100:.0f}%` de chance do vencedor "
            "não levar **nada**, mesmo ganhando — é sorte pura!\n\n"
            "**4️⃣ Desbloqueando criaturas**\n"
            "Toda criatura tem uma **raridade** — ⚪ Comum, 🔵 Raro, 🟣 Épico, 🟡 Lendário, 🌀 Elemental, 🐺 Bestas, "
            "🦴 Fóssil, 🌌 Secreto ou 🐉 Mítico — e quanto mais rara, menos ela costuma aparecer nos sorteios. Todo "
            "mundo já começa com as ⚪ Comuns desbloqueadas; Raras, Épicas e Lendárias saem **de recompensa** pra "
            "quem **vence** uma batalha — o jogo sorteia uma criatura nova (que você ainda não tem) e ela entra "
            "pra sua coleção pra sempre. Quem perde não ganha nada disso. 🌀 Elementais, 🐺 Bestas, 🦴 Fósseis, "
            "🌌 Secretas e 🐉 Míticas seguem caminhos próprios pra desbloquear — veja os itens 8️⃣, 9️⃣, 🔟 e 1️⃣2️⃣ "
            "abaixo. Veja a lista completa na 📖 **Enciclopédia** (mensagem fixa aqui embaixo) e confira sua "
            "coleção com `.criaturas`.\n\n"
            "**5️⃣ ⭐ Nível de Capacidade — quanto mais usa, mais forte fica**\n"
            "Além da raridade, toda criatura tem um **Nível de Capacidade** individual (de 1 a "
            f"{_NIVEL_CRIATURA_MAX}), que é **por pessoa**. Ela sempre começa no Nível 1, e cada vez que "
            "você a invoca numa batalha — ganhando ou perdendo, não importa — ela ganha experiência e "
            "pode subir de nível, até o teto. Ou seja: se duas pessoas tiverem a MESMA criatura, mas uma "
            "já batalhou muito mais com ela, a mais usada leva vantagem no confronto, mesmo sendo a "
            "mesma raridade. Confira o nível de cada uma sua com `.criaturas`.\n\n"
            "**6️⃣ 🌟 Criatura favorita**\n"
            "Use `.favorito <nome da criatura>` pra escolher uma favorita entre as que você já tem — "
            "a partir daí, ela é **sempre** a escolhida nas suas batalhas, sem sorteio nenhum. Só que "
            f"depois de `{_FAVORITO_USOS_ATE_CANSAR}` usos seguidos ela **cansa**: some da jogada, suas "
            "batalhas voltam a sortear aleatoriamente, e ela entra num cooldown de "
            f"`{_FAVORITO_COOLDOWN_SEGUNDOS // 60} min` até poder ser favoritada de novo (ou você pode "
            "trocar de favorita a qualquer momento com `.favorito <outro nome>`, ou tirar com "
            "`.favorito remover`). Veja `.favorito` sozinho pra conferir o status atual.\n\n"
            "**7️⃣ ⚔️ Hierarquia de força das raridades**\n"
            "Raridade mais alta = criatura mais forte, mas ninguém fica sem chance nenhuma! "
            "A cada raridade de distância entre as duas criaturas, a chance da mais forte sobe um "
            "degrau — só que a mais fraca **sempre** mantém uma chance real de dar a zebra:\n"
            f"⚪↔🔵 **1 raridade de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[1]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[1])*100:.0f}%`\n"
            f"⚪↔🟣 **2 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[2]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[2])*100:.0f}%`\n"
            f"⚪↔🟡 **3 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[3]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[3])*100:.0f}%`\n"
            f"⚪↔🐺 **4 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[4]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[4])*100:.0f}%`\n"
            f"⚪↔🦴 **5 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[5]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[5])*100:.0f}%`\n"
            f"⚪↔🌌 **6 raridades de distância:** `{_CHANCE_VITORIA_POR_DEGRAU[6]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[6])*100:.0f}%`\n"
            f"⚪↔🐉 **7 raridades de distância (máxima):** `{_CHANCE_VITORIA_POR_DEGRAU[7]*100:.0f}%` x `{(1-_CHANCE_VITORIA_POR_DEGRAU[7])*100:.0f}%`\n"
            f"Mesma raridade (ex: Épico vs Épico) é sempre `{_CHANCE_VITORIA_POR_DEGRAU[0]*100:.0f}%` x "
            f"`{_CHANCE_VITORIA_POR_DEGRAU[0]*100:.0f}%` como ponto de partida — e o Nível de Capacidade de "
            f"cada criatura (item acima) ainda refina esse número um pouco pra cima ou pra baixo.\n"
            f"⚠️ **Excepção:** 🟡 Lendário vs 🐉 Mítico e 🟡 Lendário vs 🌌 Secreto não seguem essa "
            f"tabela por degraus — a discrepância aqui é bem maior que em qualquer outro confronto:\n"
            f"🟡↔🐉 **Lendário vs Mítico:** `{_CHANCE_VITORIA_LENDARIO_MITICO*100:.0f}%` x "
            f"`{(1-_CHANCE_VITORIA_LENDARIO_MITICO)*100:.0f}%`\n"
            f"🟡↔🌌 **Lendário vs Secreto:** `{_CHANCE_VITORIA_LENDARIO_SECRETO*100:.0f}%` x "
            f"`{(1-_CHANCE_VITORIA_LENDARIO_SECRETO)*100:.0f}%`\n\n"
            "**8️⃣ 🐺 Bestas — a recompensa de quem treina de verdade**\n"
            "Mais fortes que as 🟡 Lendárias, mas ainda um degrau abaixo das 🌌 Secretas. Não saem de nenhum "
            "sorteio — a ÚNICA forma de conseguir uma é levando uma criatura ⚪ Comum, 🔵 Raro, 🟣 Épico ou 🟡 Lendário até o "
            f"Nível de Capacidade máximo (`{_NIVEL_CRIATURA_MAX}`, item 5️⃣ acima). Ao bater esse nível, você ganha, "
            "na hora e de graça, 1 Besta sorteada entre as do tier correspondente que você ainda não tiver — "
            "garantido, sem depender de sorte nenhuma!\n\n"
            "**9️⃣ 🐉 Míticos — os dragões**\n"
            "A raridade mais forte de todas, e também a mais rara de conseguir: não entram no sorteio "
            f"normal — a cada `{_MITICO_VITORIAS_INTERVALO}` vitórias suas, rola uma chance de só "
            f"`{_MITICO_CHANCE_DESBLOQUEIO * 100:.0f}%` de destravar um.\n\n"
            "**🔟 🦴 Fósseis — só desenterrados em call**\n"
            "Um degrau abaixo das 🌌 Secretas, mas mais fortes que as 🟡 Lendárias. Não entram no sorteio "
            "normal, no 🪙 Baú nem no `.ovo` — a ÚNICA forma de conseguir um é **vencendo** uma batalha de "
            "desafio com você **E** a pessoa que te desafiou (ou que você desafiou) **os dois numa call de "
            f"voz** no momento em que a batalha termina. Só nessas condições rola uma chance de "
            f"`{_FOSSIL_CHANCE_DESBLOQUEIO * 100:.0f}%` de desenterrar um Fóssil novo — se algum dos dois "
            "não estiver em call, a rolagem nem acontece.\n\n"
            "**1️⃣1️⃣ 🐾 Pets — companheiros de suporte contra Boss**\n"
            f"Leve uma criatura 🔵 Rara até o Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}` e "
            "ganhe, de graça, um Pet sorteado. Pets não batalham no PvP — são suporte: EQUIPADOS "
            f"(`.equiparpet <nome>`), somam entre `{_PET_BONUS_BOSS_NIVEL1*100:.0f}%` e "
            f"`{_PET_BONUS_BOSS_NIVEL5*100:.0f}%` na chance de vencer qualquer Boss (conforme o "
            "Nível do Pet, de 1 a 5) e têm chance de upar uma das suas criaturas depois de uma "
            "vitória. Só sobem de Nível enfrentando Boss, e cada um destrava uma habilidade "
            "especial própria no Nível 3. Veja todos na 📖 Enciclopédia!\n\n"
            "**1️⃣2️⃣ 🌀 Elementais — o prêmio de quem evolui uma Épica**\n"
            "Mais fortes que as 🟡 Lendárias, mas ainda um degrau abaixo das 🐺 Bestas. A única forma de "
            f"conseguir um é levando uma criatura 🟣 Épica até o **Nível de Capacidade `{_ELEMENTAL_NIVEL_DESBLOQUEIO}`** "
            "(não precisa ser o teto) — ao bater esse nível, você recebe, na hora e de graça, 1 Elemental "
            "sorteado entre os 12 que ainda não tiver (sem distinção de tier, todos entram no mesmo sorteio). "
            "E não para aí: toda vez que um Elemental for convocado numa batalha de desafio — ganhando ou "
            "perdendo, não importa — quem o convocou ganha, na hora, um **Booster de xp em dobro** por "
            f"`{_ELEMENTAL_BOOSTER_MINUTOS} min` (empilha em cima de qualquer outro booster já ativo). Todo "
            f"desbloqueio de Elemental é anunciado em <#{_BESTA_ANUNCIO_CANAL_ID}>. ⚡\n\n"
            "**1️⃣3️⃣ Pra poder batalhar**\n"
            "Os dois precisam ter o cargo do ranking de nível e já ter algum XP acumulado. "
            f"E cada pessoa só pode lançar um novo desafio a cada `{_BATALHA_COOLDOWN_SEGUNDOS // 60} min`.\n\n"
            "💨 *Todas as mensagens da batalha (convite, criaturas e resultado) somem sozinhas "
            f"depois de `{_BATALHA_TEMPO_SOMEM}s` — não fica lixo acumulando no chat!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xe8d5f5,
    )
    embed.set_footer(text="👽 Renan — Arena de Batalhas")
    return embed


async def _achar_mensagem_info_batalha(canal: discord.TextChannel):
    """Varre o histórico do canal, apaga explicações de batalha duplicadas
    antigas (deixando só a mais recente) e devolve essa mensagem pra ser editada."""
    mensagens = []
    try:
        async for msg in canal.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == _XP_BATALHA_INFO_TITULO:
                mensagens.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return None

    if not mensagens:
        return None

    mais_recente, *duplicadas = mensagens
    for dup in duplicadas:
        try:
            await dup.delete()
        except discord.HTTPException:
            pass
    return mais_recente


async def _atualizar_info_batalha(canal: discord.TextChannel) -> None:
    """Garante que a mensagem explicando as batalhas fique sempre logo abaixo
    da mensagem de escolha de cor (fixa, editada, nunca duplicada)."""
    global _xp_batalha_info_message_id

    embed = _montar_embed_info_batalha()

    mensagem = None
    if _xp_batalha_info_message_id:
        try:
            mensagem = await canal.fetch_message(_xp_batalha_info_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            mensagem = None

    if mensagem is None:
        mensagem = await _achar_mensagem_info_batalha(canal)

    if mensagem:
        try:
            await mensagem.edit(embed=embed)
            _xp_batalha_info_message_id = mensagem.id
            return
        except discord.HTTPException as e:
            print(f"[ranking-xp] ERRO ao editar mensagem de explicação de batalha: {e!r}")
            mensagem = None

    try:
        nova = await canal.send(embed=embed)
        _xp_batalha_info_message_id = nova.id
        print(f"[ranking-xp] Mensagem de explicação de batalha criada em #{canal.name} (id {nova.id}).")
    except discord.HTTPException as e:
        print(f"[ranking-xp] ERRO ao enviar mensagem de explicação de batalha em #{canal.name}: {e!r}")


# ══════════════════════════════════════════════════════════════════════
# ENCICLOPÉDIA DE CRIATURAS — fica por ÚLTIMO no canal de ranking, embaixo
# de tudo (ranking, cor e explicação de batalha). Lista todas as criaturas
# que existem, agrupadas por raridade. Cada pessoa pode usar o menu de
# seleção pra ver os detalhes (imagem) de uma criatura e conferir, de forma
# privada (ephemeral), se ELA MESMA já desbloqueou aquela criatura ou não.
# ══════════════════════════════════════════════════════════════════════

_XP_ENCICLOPEDIA_TITULO = "📖 Enciclopédia de Criaturas"


def _montar_embed_enciclopedia() -> discord.Embed:
    """Monta o embed geral da Enciclopédia: todas as criaturas existentes,
    agrupadas por raridade (da mais rara pra mais comum)."""
    embed = discord.Embed(
        title=_XP_ENCICLOPEDIA_TITULO,
        description=(
            "👽 **Renan:** ...toda criatura que já apareceu (ou pode aparecer) na Arena de Batalhas "
            "mora aqui. Todo mundo começa com as ⚪ Comuns. Só dá pra invocar em batalha o que você já "
            "tem — vença combates e, de recompensa, destrave uma criatura nova pra coleção. Os 🐉 "
            "MÍTICOS são outro nível: quase imbatíveis contra qualquer raridade menor, mas raríssimos "
            "de conseguir — só numa chance bem pequena a cada várias vitórias. As 🌌 Secretas nem essas "
            "vitórias concedem; só saem do 🪙 Baú, com uma chance minúscula — as mais raras de todas. "
            "Os 🦴 FÓSSEIS só aparecem pra quem tá de call: vença uma batalha com os dois lados numa "
            "call de voz, e rola uma chancezinha de desenterrar um. As 🐺 BESTAS não vêm de sorte "
            "nenhuma — é pura conquista: leva uma "
            f"criatura ⚪🔵🟣🟡 até o Nível de Capacidade máximo (`{_NIVEL_CRIATURA_MAX}`) e ela é sua, garantido.\n\n"
            "...e os 🌀 ELEMENTAIS só chegam pra quem leva uma 🟣 Épica até o Nível de Capacidade "
            f"`{_ELEMENTAL_NIVEL_DESBLOQUEIO}` — sem sorteio, pura conquista. E cada Elemental usado em batalha "
            "ainda concede, na hora, um Booster de xp em dobro pra quem o convocou.\n\n"
            "👇 Use o menu abaixo pra escolher uma raridade — ele abre, só pra você, as criaturas "
            "daquela raridade pra conferir os detalhes (e a imagem) de cada uma."
        ),
        color=0x9b59b6,
    )
    for raridade in _ORDEM_RARIDADES:
        info = _RARIDADES[raridade]
        nomes = [c["nome"] for c in _BATALHA_CRIATURAS if c["raridade"] == raridade]
        if not nomes:
            continue
        embed.add_field(
            name=f"{info['emoji']} {info['label']} ({len(nomes)})",
            value="\n".join(f"• {nome}" for nome in nomes),
            inline=False,
        )

    embed.add_field(
        name=f"🐾 Pets ({len(_PETS)})",
        value=(
            "\n".join(f"• {p['nome']}" for p in _PETS) + "\n\n"
            f"Desbloqueados ao levar uma criatura 🔵 Rara até o Nível de Capacidade "
            f"`{_PET_NIVEL_DESBLOQUEIO}` — não entram em batalha, são SUPORTE: quando equipados "
            "(`.equiparpet <nome>`), somam bônus na chance de vencer Boss e podem upar suas "
            "criaturas. Confira os detalhes de cada um no menu abaixo!"
        ),
        inline=False,
    )

    embed.set_footer(text=f"👽 Renan — {len(_BATALHA_CRIATURAS)} criaturas e {len(_PETS)} pets ao todo")
    return embed


class EnciclopediaSelect(discord.ui.Select):
    """Menu de seleção com as criaturas de UMA raridade. Ao escolher uma, a
    pessoa recebe (de forma privada) a imagem, a raridade e se JÁ desbloqueou
    aquela criatura.

    Existe um select por raridade (em vez de um único com todas as criaturas)
    porque o Discord só permite até 25 opções por menu — dividindo por
    raridade, cada menu tem bastante folga pra coleção continuar crescendo."""

    def __init__(self, raridade: str):
        self.raridade = raridade
        info = _RARIDADES[raridade]
        criaturas_da_raridade = [c for c in _BATALHA_CRIATURAS if c["raridade"] == raridade][:25]
        options = [
            discord.SelectOption(
                label=c["nome"][:100],
                value=c["id"],
                description=info["label"],
                emoji=info["emoji"],
            )
            for c in criaturas_da_raridade
        ]
        super().__init__(
            placeholder=f"{info['emoji']} Ver criaturas {info['label']}s...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"enciclopedia_criaturas_select_{raridade}",
        )

    async def callback(self, interaction: discord.Interaction):
        criatura = next((c for c in _BATALHA_CRIATURAS if c["id"] == self.values[0]), None)
        if criatura is None:
            await interaction.response.send_message("⚠️ Criatura não encontrada.", ephemeral=True)
            return

        desbloqueada = criatura["id"] in set(_garantir_criaturas_iniciais(interaction.user.id))
        info_raridade = _RARIDADES[criatura["raridade"]]

        if desbloqueada:
            nivel_pessoal = _nivel_criatura(interaction.user.id, criatura["id"])
            status = (
                "🔓 **Você já desbloqueou essa criatura!** Ela pode aparecer nas suas batalhas.\n"
                f"⭐ **Nível de Capacidade atual:** `{nivel_pessoal}/{_nivel_criatura_max(criatura['id'])}` — "
                "use ela em mais batalhas pra deixar cada vez mais forte."
            )
        else:
            status = (
                "🔒 **Você ainda não desbloqueou essa criatura.** "
                "Vença batalhas usando as que você já tem — como recompensa, "
                "há chance dela ser sorteada e ir pra sua coleção!"
            )

        embed = discord.Embed(
            title=f"{info_raridade['emoji']} {criatura['nome']}",
            description=f"**Raridade:** {info_raridade['label']}\n\n{status}",
            color=info_raridade["cor"],
        )
        embed.set_image(url=criatura["gif"])
        embed.set_footer(text="👽 Renan — Enciclopédia de Criaturas")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class EnciclopediaRaridadeSelect(discord.ui.Select):
    """Passo 1 da navegação: escolher qual raridade explorar. Ao escolher,
    abre — só pra quem clicou — o menu com as criaturas daquela raridade
    (EnciclopediaSelect). Isso existe como um passo à parte (em vez de um
    select por raridade direto na mensagem fixa) porque o Discord só permite
    5 menus por mensagem, e com 8 raridades (contando 🦴 Fóssil e 🌌 Secreta) não
    caberia mais um select fixo por raridade — assim sobra espaço mesmo se
    surgirem raridades novas no futuro."""

    def __init__(self):
        options = []
        for raridade in _ORDEM_RARIDADES:
            if not any(c["raridade"] == raridade for c in _BATALHA_CRIATURAS):
                continue
            info = _RARIDADES[raridade]
            qtd = sum(1 for c in _BATALHA_CRIATURAS if c["raridade"] == raridade)
            options.append(
                discord.SelectOption(
                    label=f"{info['label']} ({qtd})",
                    value=raridade,
                    emoji=info["emoji"],
                )
            )
        super().__init__(
            placeholder="🔍 Escolha uma raridade pra explorar...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="enciclopedia_raridade_select",
        )

    async def callback(self, interaction: discord.Interaction):
        raridade = self.values[0]
        info = _RARIDADES[raridade]
        view = discord.ui.View(timeout=180)
        view.add_item(EnciclopediaSelect(raridade))
        await interaction.response.send_message(
            f"{info['emoji']} Escolha uma criatura **{info['label']}** pra ver os detalhes:",
            view=view,
            ephemeral=True,
        )


class EnciclopediaPetsSelect(discord.ui.Select):
    """Menu de seleção com todos os 🐾 Pets — como são só 8 (bem abaixo do
    limite de 25 opções do Discord), não precisa de um passo intermediário
    por raridade, igual as criaturas. Ao escolher um, a pessoa recebe (de
    forma privada) a imagem, se já desbloqueou, o Nível atual e a
    habilidade especial dele."""

    def __init__(self):
        options = [
            discord.SelectOption(label=p["nome"][:100], value=p["id"], emoji="🐾")
            for p in _PETS
        ]
        super().__init__(
            placeholder="🐾 Ver detalhes de um Pet...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="enciclopedia_pets_select",
        )

    async def callback(self, interaction: discord.Interaction):
        pet = next((p for p in _PETS if p["id"] == self.values[0]), None)
        if pet is None:
            await interaction.response.send_message("⚠️ Pet não encontrado.", ephemeral=True)
            return

        desbloqueado = pet["id"] in set(_pets_desbloqueados(interaction.user.id))

        if desbloqueado:
            nivel_pessoal = _nivel_pet(interaction.user.id, pet["id"])
            equipado = xp_stats[interaction.user.id].get("pet_equipado") == pet["id"]
            status = (
                "🔓 **Você já tem esse Pet!**" + (" 🐾 *(equipado agora)*" if equipado else "") + "\n"
                f"⭐ **Nível atual:** `{nivel_pessoal}/{_PET_NIVEL_MAX}` — só sobe enfrentando Boss.\n\n"
                f"**{pet['habilidade_nome']}** (destrava no Nível `{_PET_NIVEL_HABILIDADE}`): "
                f"{pet['habilidade_descricao']}"
                + ("\n\n✨ *Habilidade já ativa!*" if nivel_pessoal >= _PET_NIVEL_HABILIDADE else "")
            )
        else:
            status = (
                "🔒 **Você ainda não desbloqueou esse Pet.** Leve uma criatura 🔵 Rara até o "
                f"Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}` — tem chance dele ser sorteado "
                "e ir pra sua coleção de graça!\n\n"
                f"**{pet['habilidade_nome']}:** {pet['habilidade_descricao']}"
            )

        embed = discord.Embed(
            title=f"🐾 {pet['nome']}",
            description=status,
            color=0x9b59b6,
        )
        embed.set_image(url=pet["gif"])
        embed.set_footer(text="👽 Renan — Enciclopédia de Pets")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class EnciclopediaView(discord.ui.View):
    """View persistente (sobrevive a reinícios do bot) com o menu pra
    escolher a raridade de criatura — que abre, de forma privada, o menu
    com as criaturas daquela raridade — e o menu de 🐾 Pets, lado a lado."""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EnciclopediaRaridadeSelect())
        self.add_item(EnciclopediaPetsSelect())


async def _achar_mensagem_enciclopedia(canal: discord.TextChannel):
    """Varre o histórico do canal, apaga Enciclopédias duplicadas antigas
    (deixando só a mais recente) e devolve essa mensagem pra ser editada."""
    mensagens = []
    try:
        async for msg in canal.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == _XP_ENCICLOPEDIA_TITULO:
                mensagens.append(msg)
    except (discord.Forbidden, discord.HTTPException):
        return None

    if not mensagens:
        return None

    mais_recente, *duplicadas = mensagens
    for dup in duplicadas:
        try:
            await dup.delete()
        except discord.HTTPException:
            pass
    return mais_recente


async def _atualizar_enciclopedia(canal: discord.TextChannel) -> None:
    """Garante que a Enciclopédia fique sempre por ÚLTIMO no canal (fixa,
    editada, nunca duplicada), embaixo do ranking, da cor e da explicação
    de batalha."""
    global _xp_enciclopedia_message_id

    embed = _montar_embed_enciclopedia()
    view = EnciclopediaView()

    mensagem = None
    if _xp_enciclopedia_message_id:
        try:
            mensagem = await canal.fetch_message(_xp_enciclopedia_message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            mensagem = None

    if mensagem is None:
        mensagem = await _achar_mensagem_enciclopedia(canal)

    if mensagem:
        try:
            await mensagem.edit(embed=embed, view=view)
            _xp_enciclopedia_message_id = mensagem.id
            return
        except discord.HTTPException as e:
            print(f"[ranking-xp] ERRO ao editar mensagem de enciclopédia: {e!r}")
            mensagem = None

    try:
        nova = await canal.send(embed=embed, view=view)
        _xp_enciclopedia_message_id = nova.id
        print(f"[ranking-xp] Mensagem de enciclopédia criada em #{canal.name} (id {nova.id}).")
    except discord.HTTPException as e:
        print(f"[ranking-xp] ERRO ao enviar mensagem de enciclopédia em #{canal.name}: {e!r}")


async def _atualizar_ranking_xp() -> None:
    """Atualiza (ou cria, se ainda não existir) as mensagens de ranking de XP.
    Normalmente é só 1 mensagem, sempre editada (fixa no topo, nunca
    duplica). Todo mundo elegível aparece — inclusive quem está no Nível 0 —
    e se a lista ficar grande demais pra caber num único embed, as páginas
    extras ficam disponíveis pelas setinhas ◀ ▶ embaixo do ranking, sem
    empilhar mensagem nenhuma.

    ⚠️ Roda inteira dentro de um lock: essa função é chamada de vários
    lugares diferentes (loop automático, level-up, troca de cor, baú,
    batalhas...), às vezes via asyncio.create_task — sem o lock, duas
    chamadas concorrentes podiam achar que a mensagem fixa ainda não existe
    (porque nenhuma das duas tinha terminado de criar) e cada uma mandava
    uma cópia nova, duplicando ranking/cor/batalha/enciclopédia no canal."""
    global _xp_ranking_message_id, _xp_ranking_pagina_atual

    async with (_xp_ranking_update_lock or asyncio.Lock()):
        guild = bot.guilds[0] if bot.guilds else None
        if guild is None:
            print("[ranking-xp] ERRO: bot não está em nenhum servidor ainda.")
            return

        canal = guild.get_channel(CANAL_XP_ID)
        if canal is None:
            print(
                f"[ranking-xp] ERRO: canal com ID {CANAL_XP_ID} não encontrado em "
                f"'{guild.name}'. Confira se o ID do canal Ranking-01 está certo."
            )
            return

        embeds = _montar_embeds_ranking_xp(guild)
        total_paginas = len(embeds)

        # A página atual pode ter ficado fora do intervalo válido (ex: o total
        # de páginas diminuiu porque alguém saiu do servidor) — trava dentro
        # do limite pra nunca dar IndexError.
        if _xp_ranking_pagina_atual >= total_paginas:
            _xp_ranking_pagina_atual = total_paginas - 1
        if _xp_ranking_pagina_atual < 0:
            _xp_ranking_pagina_atual = 0

        embed_atual = embeds[_xp_ranking_pagina_atual]
        view = RankingXPView(total_paginas=total_paginas)

        mensagem = None
        if _xp_ranking_message_id:
            try:
                mensagem = await canal.fetch_message(_xp_ranking_message_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                mensagem = None

        if mensagem is None:
            # Procura no histórico — inclui achar páginas antigas empilhadas de
            # antes das setinhas existirem, pra ficar só com a mais antiga (as
            # extras são apagadas, já que agora tudo cabe numa mensagem só).
            candidatas = await _achar_mensagens_ranking_xp(canal)
            if candidatas:
                mensagem, *extras = candidatas
                for extra in extras:
                    try:
                        await extra.delete()
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        pass

        if mensagem:
            try:
                await mensagem.edit(embed=embed_atual, view=view)
                _xp_ranking_message_id = mensagem.id
            except discord.HTTPException as e:
                print(f"[ranking-xp] ERRO ao editar mensagem do ranking: {e!r}")
                mensagem = None

        if mensagem is None:
            try:
                nova = await canal.send(embed=embed_atual, view=view)
                _xp_ranking_message_id = nova.id
                print(f"[ranking-xp] Mensagem do ranking criada em #{canal.name} (id {nova.id}).")
            except discord.HTTPException as e:
                print(f"[ranking-xp] ERRO ao enviar mensagem do ranking em #{canal.name}: {e!r}")

        # Mantém o menu de escolha de cor sempre fixo logo abaixo do ranking
        try:
            await _atualizar_pergunta_cor(canal)
        except Exception as e:
            print(f"[ranking-xp] ERRO ao atualizar mensagem de escolha de cor: {e!r}")

        # Mantém a explicação da mecânica de batalhas fixa logo abaixo da de cor
        try:
            await _atualizar_info_batalha(canal)
        except Exception as e:
            print(f"[ranking-xp] ERRO ao atualizar mensagem de explicação de batalha: {e!r}")

        # Mantém a Enciclopédia de Criaturas fixa por ÚLTIMO, embaixo de tudo
        try:
            await _atualizar_enciclopedia(canal)
        except Exception as e:
            print(f"[ranking-xp] ERRO ao atualizar mensagem de enciclopédia: {e!r}")

        await _salvar_xp_stats()


_XP_POR_TICK_CALL = 12   # xp ganho a cada 1 min em call de voz — dobrado de novo (era 6, antes disso era 2)

# Calls com xp bônus — canal_id -> multiplicador aplicado em cima do
# _XP_POR_TICK_CALL normal. Qualquer call que não estiver aqui usa o valor
# padrão (1x). Não afeta calls privadas, essas continuam sem xp nenhum.
_XP_CALLS_MULTIPLICADOR = {
    1284260386635251713: 3.0,   # o triplo de xp por minuto comparado às outras calls
}


# ── Booster de Call (streak) ────────────────────────────────────────────────
# Enquanto a pessoa fica numa MESMA call de voz, sem sair, sem mutar (nem por
# si mesma nem pelo servidor) e sem trocar de canal, o xp de call dela sobe
# de nível a cada _CALL_BOOSTER_INTERVALO_MINUTOS minutos: nível 1 = xp normal,
# nível 2 = xp em dobro, nível 3 = triplo, e assim por diante, sem limite.
# Qualquer uma dessas ações reseta o booster NA HORA, de volta pro nível 1:
#   • sair da call
#   • mutar (self-mute ou mute pelo servidor)
#   • trocar de canal de voz (mesmo pra outra call válida)
# Toda vez que o nível sobe, um aviso aparece no canal CANAL_XP_ID dizendo
# que o Booster de Call daquela pessoa foi ativado — e some sozinho depois
# de 1 minuto (mesmo canal e mesmo estilo do aviso de Level Up).
_CALL_BOOSTER_INTERVALO_MINUTOS = 20

_CALL_BOOSTER_DATA_FILE = os.path.join(_RPG_DATA_DIR, "call_booster_data.json")

_call_booster_inicio: dict = {}            # user_id -> time.time() de quando a streak ATUAL começou (ininterrupta)
_call_booster_nivel_anunciado: dict = {}   # user_id -> último nível (x2, x3, x4...) já avisado no canal, pra não repetir


def _carregar_call_booster_stats() -> None:
    """Carrega a streak do Booster de Call salva em disco (na pasta do volume,
    _RPG_DATA_DIR), se existir. Roda antes do bot conectar — é isso que
    permite a streak de quem já estava numa call sobreviver a um reinício
    do bot (Railway ou qualquer outro), em vez de voltar pro nível 1 na hora.
    A reconciliação final (quem realmente ainda está numa call válida agora)
    acontece no on_ready, depois que o bot já sabe quem está conectado."""
    if not os.path.exists(_CALL_BOOSTER_DATA_FILE):
        return
    try:
        with open(_CALL_BOOSTER_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for uid_str, inicio in dados.get("inicio", {}).items():
            _call_booster_inicio[int(uid_str)] = inicio
        for uid_str, nivel in dados.get("nivel_anunciado", {}).items():
            _call_booster_nivel_anunciado[int(uid_str)] = nivel
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_call_booster_stats() -> None:
    """Salva a streak do Booster de Call em disco de forma atômica (escreve em
    .tmp e substitui) — pra não perder o progresso quando o bot reiniciar."""
    dados = {
        "inicio": {str(uid): inicio for uid, inicio in _call_booster_inicio.items()},
        "nivel_anunciado": {str(uid): nivel for uid, nivel in _call_booster_nivel_anunciado.items()},
    }
    tmp_path = _CALL_BOOSTER_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_RPG_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _CALL_BOOSTER_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_xp_stats_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


def _nivel_call_booster(user_id: int) -> int:
    """Nível atual do Booster de Call de alguém: 1 = sem boost (xp de call normal),
    2 = xp de call em dobro, 3 = triplo... sobe 1 nível a cada
    _CALL_BOOSTER_INTERVALO_MINUTOS minutos ininterruptos numa mesma call.
    Sem streak ativa agora (não está numa call qualificada), devolve 1 (sem efeito)."""
    inicio = _call_booster_inicio.get(user_id)
    if inicio is None:
        return 1
    minutos_corridos = (time.time() - inicio) / 60
    return 1 + int(minutos_corridos // _CALL_BOOSTER_INTERVALO_MINUTOS)


def _resetar_call_booster(user_id: int) -> None:
    """Zera a streak do Booster de Call de alguém — perde o multiplicador na
    hora (saiu da call, mutou, ou trocou de canal)."""
    tinha_streak = user_id in _call_booster_inicio
    _call_booster_inicio.pop(user_id, None)
    _call_booster_nivel_anunciado.pop(user_id, None)
    if tinha_streak:
        asyncio.create_task(_salvar_call_booster_stats())


def _iniciar_call_booster(user_id: int) -> None:
    """Começa (ou reinicia do zero) a contagem da streak do Booster de Call."""
    _call_booster_inicio[user_id] = time.time()
    _call_booster_nivel_anunciado[user_id] = 1
    asyncio.create_task(_salvar_call_booster_stats())


def _empilhar_call_booster(user_id: int, ciclos: int = 1) -> None:
    """Adianta o relógio da streak do Booster de Call de alguém em `ciclos`
    intervalos inteiros de _CALL_BOOSTER_INTERVALO_MINUTOS — na prática,
    empilha +1 nível de booster por ciclo EM CIMA do que a pessoa já tiver
    (se ela já estiver numa streak de verdade, soma tempo a mais nela em vez
    de resetar; se não tiver nenhuma rodando, começa uma nova já adiantada)."""
    avanco_segundos = ciclos * _CALL_BOOSTER_INTERVALO_MINUTOS * 60
    inicio_atual = _call_booster_inicio.get(user_id, time.time())
    _call_booster_inicio[user_id] = inicio_atual - avanco_segundos
    asyncio.create_task(_salvar_call_booster_stats())


async def _anunciar_call_booster(guild: discord.Guild, membro: discord.Member, nivel: int) -> None:
    """Avisa no canal de XP que o Booster de Call de alguém subiu pro nível
    informado (x2, x3, x4...). O aviso some sozinho depois de 1 minuto."""
    canal = guild.get_channel(CANAL_XP_ID)
    if canal is None:
        return

    embed = discord.Embed(
        title="🔥 Booster de Call ativado!",
        description=(
            f"⚡ {membro.mention} ficou tempo suficiente numa call sem sair, sem mutar e sem trocar "
            f"de canal — o xp de call agora está em **`x{nivel}`**!\n\n"
            "👽 **Renan:** ...continue na call que aumenta ainda mais. Saia, troque de call ou mute, "
            "e o booster desaparece na hora."
        ),
        color=0xff8c42,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text="👽 Renan — Booster de Call • some em 1 minuto")

    try:
        msg = await canal.send(embed=embed)
        asyncio.create_task(_apagar_mensagem_depois(msg, 60))
    except discord.HTTPException:
        pass


async def _processar_call_booster_voice(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    """Controla a streak do Booster de Call a partir de cada mudança de estado
    de voz: começa a contar quando a pessoa entra numa call válida (não-privada)
    e desmutada, e reseta na hora se ela sair da call, mutar (self ou servidor)
    ou trocar de canal de voz."""
    if member.bot:
        return

    try:
        canal_antes = before.channel
        canal_depois = after.channel
        mutado_depois = bool(after.self_mute or after.mute)

        # Saiu da call inteiramente -> perde o booster na hora
        if canal_depois is None:
            _resetar_call_booster(member.id)
            return

        # Trocou de canal de voz -> perde o booster na hora, mesmo indo pra outra call válida
        trocou_de_canal = canal_antes is not None and canal_antes.id != canal_depois.id
        if trocou_de_canal:
            _resetar_call_booster(member.id)

        # Calls privadas não participam do booster de call (mesma regra do xp de call)
        if canal_depois.id in _XP_CALLS_PRIVADAS:
            _resetar_call_booster(member.id)
            return

        if mutado_depois:
            # Mutou agora (self-mute ou mute pelo servidor) -> perde o booster na hora
            _resetar_call_booster(member.id)
            return

        # Está numa call válida e desmutada: se não tinha streak rodando
        # (acabou de entrar, de trocar de canal, ou de desmutar), começa do zero.
        if _call_booster_inicio.get(member.id) is None:
            _iniciar_call_booster(member.id)
    except Exception as e:
        print(f"[booster-call] ERRO ao processar {member} ({member.id}): {e!r}")


async def _processar_xp_call(guild: discord.Guild) -> None:
    """A cada 1 minuto (mesmo ritmo do loop de ranking), dá um pouco de xp pra
    quem está numa call de voz agora. É só um reforço — bem menos do que
    mandar mensagem nos canais principais, mas já soma algo. Destravado pra
    todo mundo, sem exigir cargo. Calls privadas (_XP_CALLS_PRIVADAS) não
    pontuam — quem está nelas é ignorado. Quem está mutado (silenciado por
    si mesmo ou pelo servidor) também não pontua — só ganha quem está de
    fato participando da call com o microfone aberto."""
    for canal_voz in guild.voice_channels:
        if canal_voz.id in _XP_CALLS_PRIVADAS:
            continue
        for membro in canal_voz.members:
            if membro.bot:
                continue

            estado_voz = membro.voice
            if estado_voz is not None and (estado_voz.self_mute or estado_voz.mute):
                continue

            ganho_call = _XP_POR_TICK_CALL * _XP_CALLS_MULTIPLICADOR.get(canal_voz.id, 1.0)
            # 🎁 Booster de XP do Baú — se estiver ativo, dobra o ganho por um tempo
            if time.time() < _xp_booster_ate.get(membro.id, 0):
                ganho_call *= _BAU_BOOSTER_MULTIPLICADOR

            # 🔥 Booster de Call — sobe 1 nível (x2, x3, x4...) a cada 20 min
            # ininterruptos na mesma call. Se acabou de subir de nível, avisa
            # no canal de XP (mensagem que some sozinha em 1 minuto).
            nivel_boost = _nivel_call_booster(membro.id)
            if nivel_boost > 1:
                ganho_call *= nivel_boost
            if nivel_boost > _call_booster_nivel_anunciado.get(membro.id, 1):
                _call_booster_nivel_anunciado[membro.id] = nivel_boost
                asyncio.create_task(_anunciar_call_booster(guild, membro, nivel_boost))
                asyncio.create_task(_salvar_call_booster_stats())

            ganho_call = max(1, round(ganho_call))

            dados = xp_stats[membro.id]
            nivel_antigo = dados["nivel"]
            dados["xp"] += ganho_call

            nivel_novo, _, _ = _calcular_nivel(dados["xp"])
            dados["nivel"] = nivel_novo

            if nivel_novo > nivel_antigo:
                await _anunciar_level_up(guild, membro, nivel_novo)


@tasks.loop(minutes=1)
async def loop_ranking_xp():
    for guild in bot.guilds:
        try:
            await _processar_xp_call(guild)
        except Exception as e:
            print(f"[ranking-xp] ERRO ao processar xp de call em '{guild.name}': {e!r}")
    await _atualizar_ranking_xp()


_VERXP_SOME_SEGUNDOS = 10   # a resposta do .verxp some sozinha depois desse tempo


@bot.command(name="verxp")
async def cmd_verxp(ctx):
    """Mostra quanto de xp por minuto você está ganhando AGORA numa call de
    voz (base + bônus da call + Booster de Baú + Booster de Call), além de
    quais boosters estão ativos (com o tempo que falta pra cada um) e há
    quanto tempo você tá nessa call sem sair/mutar/trocar de canal. Usa a
    mesma conta de verdade de _processar_xp_call. A resposta some sozinha
    em alguns segundos. Uso: .verxp"""
    autor = ctx.author

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        aviso = await ctx.send("⚠️ Esse comando só funciona dentro do servidor.")
        await _apagar_mensagem_depois(aviso, _VERXP_SOME_SEGUNDOS)
        return

    membro = guild.get_member(autor.id)
    if membro is None:
        try:
            membro = await guild.fetch_member(autor.id)
        except discord.NotFound:
            membro = None

    estado_voz = membro.voice if membro else None
    canal_voz = estado_voz.channel if estado_voz else None

    if canal_voz is None:
        resposta = (
            "👽 **Renan:** ...você não está em nenhuma call agora. Sem call, sem xp de call — "
            f"entre numa pra começar a ganhar (base: `{_XP_POR_TICK_CALL}` xp/min)."
        )
    elif canal_voz.id in _XP_CALLS_PRIVADAS:
        resposta = "👽 **Renan:** ...essa call é privada. Não rende xp nenhum — por aqui, eu não conto."
    elif estado_voz.self_mute or estado_voz.mute:
        resposta = (
            "👽 **Renan:** ...você está mutado. Sem microfone aberto, sem xp de call — "
            "desmute pra voltar a ganhar."
        )
    else:
        agora = time.time()

        # Tempo contínuo nessa call — mesma streak usada pelo Booster de Call
        # (zera se a pessoa sair, mutar ou trocar de canal, então reflete
        # certinho "há quanto tempo você tá aqui, participando de verdade").
        inicio_streak = _call_booster_inicio.get(autor.id)
        tempo_na_call = (agora - inicio_streak) if inicio_streak else 0.0

        ganho_call = _XP_POR_TICK_CALL
        detalhes = [f"Base: `{_XP_POR_TICK_CALL}` xp/min"]

        mult_canal = _XP_CALLS_MULTIPLICADOR.get(canal_voz.id, 1.0)
        ganho_call *= mult_canal
        if mult_canal != 1.0:
            detalhes.append(f"Bônus dessa call: `x{mult_canal:g}`")

        bau_restante = _xp_booster_ate.get(autor.id, 0) - agora
        if bau_restante > 0:
            ganho_call *= _BAU_BOOSTER_MULTIPLICADOR
            detalhes.append(
                f"🎁 Booster de Baú ativo: `x{_BAU_BOOSTER_MULTIPLICADOR}` "
                f"(dura mais `{_formatar_tempo_restante(bau_restante)}`)"
            )

        nivel_boost = _nivel_call_booster(autor.id)
        if nivel_boost > 1:
            ganho_call *= nivel_boost
            intervalo_segundos = _CALL_BOOSTER_INTERVALO_MINUTOS * 60
            falta_prox_nivel = intervalo_segundos - (tempo_na_call % intervalo_segundos)
            detalhes.append(
                f"🔥 Booster de Call: `x{nivel_boost}` (nível {nivel_boost} — sobe pra "
                f"`x{nivel_boost + 1}` em `{_formatar_tempo_restante(falta_prox_nivel)}`)"
            )

        if bau_restante <= 0 and nivel_boost <= 1:
            detalhes.append("Nenhum booster ativo agora.")

        ganho_final = max(1, round(ganho_call))

        resposta = (
            f"👽 **Renan:** Agora você está ganhando **`{ganho_final}` xp por minuto** nessa call.\n"
            f"› Tempo nessa call: `{_formatar_tempo_restante(tempo_na_call)}`\n"
            + "\n".join(f"› {linha}" for linha in detalhes)
        )

    msg = await ctx.send(resposta)
    await _apagar_mensagem_depois(msg, _VERXP_SOME_SEGUNDOS)


@bot.command(name="nivel")
async def cmd_nivel(ctx, membro: discord.Member = None):
    """Mostra o nível e XP de um membro (ou de quem usou o comando). Uso: .nivel [@membro]"""
    if ctx.guild is None:
        return

    membro = membro or ctx.author
    dados_calc = xp_stats.get(membro.id, {"xp": 0, "nivel": 0, "elegivel": False, "cor": _COR_PADRAO})
    nivel, xp_no_nivel, xp_necessario = _calcular_nivel(dados_calc["xp"])
    barra = _barra_progresso(xp_no_nivel, xp_necessario, cor_emoji=_emoji_da_cor(dados_calc.get("cor", _COR_PADRAO)))

    # Entra no ranking quem já mandou mensagem em algum dos canais elegíveis
    # (_XP_CANAIS_RANKING, que inclui o chat geral) — nem que seja só uma.
    status_ranking = (
        "✅ Aparece no ranking fixo"
        if dados_calc.get("elegivel")
        else f"❌ Ainda não aparece — mande uma mensagem em <#{_XP_CANAL_1}>, "
             f"<#{_XP_CANAL_BONUS}> ou <#{_XP_CANAL_3}>"
    )

    embed = discord.Embed(
        title=f"⭐ Nível de {membro.display_name}",
        description=(
            f"**Nível:** `{nivel}`\n"
            f"**Progresso:** {barra} `{xp_no_nivel}/{xp_necessario}`\n"
            f"**XP total:** `{dados_calc['xp']}`\n"
            f"**Status no ranking:** {status_ranking}"
        ),
        color=0xe8d5f5
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text="👽 Renan — Sistema de Nível")
    await ctx.send(embed=embed)


@bot.command(name="darlevel")
async def cmd_dar_level(ctx, membro: discord.Member = None, nivel: int = None):
    """Define manualmente o nível de alguém no ranking de XP (ajusta o XP
    dela pro início desse nível). Só o Reality pode usar.
    Uso: .darlevel @membro <nível>"""
    if ctx.author.id != CRIADOR_ID:
        return

    if membro is None or nivel is None:
        await ctx.send("⚠️ Uso correto: `.darlevel @membro <nível>`\nExemplo: `.darlevel @Fulano 10`")
        return

    if nivel < 0:
        await ctx.send("⚠️ O nível não pode ser negativo.")
        return

    dados = xp_stats[membro.id]
    nivel_antigo = dados["nivel"]

    dados["xp"] = _xp_total_para_nivel(nivel)
    dados["nivel"] = nivel
    dados["elegivel"] = True  # já que ganhou um nível "oficial", passa a aparecer no ranking fixo

    await _salvar_xp_stats()
    await _atualizar_ranking_xp()

    if nivel > nivel_antigo and ctx.guild is not None:
        await _anunciar_level_up(ctx.guild, membro, nivel)

    await ctx.send(
        f"✅ **{membro.display_name}** agora está no **nível `{nivel}`** "
        f"(`{dados['xp']}` XP) — ranking já atualizado."
    )


@bot.command(name="removerxp")
async def cmd_removerxp(ctx, modo: str = None, user_id: int = None, valor: int = None):
    """Remove uma quantidade de XP BRUTO (pontos, não 'níveis' da curva) de um
    membro, identificado pelo ID — funciona mesmo se a pessoa não estiver
    mencionável/no cache. É uma subtração direta e literal: se a pessoa tem
    10.000 e você tira 2.000, ela fica com 8.000 — sem nenhum arredondamento
    pro início de nível. O nível exibido é só recalculado depois, a partir do
    XP que sobrou (nunca fica negativo — mínimo é 0). Só o Reality pode usar.
    Uso: .removerxp id <ID> <valor>
    Exemplo: .removerxp id 769951556388257812 2000   → remove 2000 pontos de XP dessa pessoa

    ⚠️ NOTA: não pode se chamar ".baumimic" — esse nome já é usado pelo baú
    disfarçado de Mimic (.baumimic) que já existe no bot, então ficaria
    duplicado e o bot recusa iniciar (CommandRegistrationError)."""
    if ctx.author.id != CRIADOR_ID:
        return

    if modo != "id" or user_id is None or valor is None:
        await ctx.send(
            "⚠️ Uso correto: `.removerxp id <ID> <valor>`\n"
            "Exemplo: `.removerxp id 769951556388257812 2000` — remove 2000 pontos de XP dessa pessoa."
        )
        return

    if valor <= 0:
        await ctx.send("⚠️ O valor de pontos (XP) a remover deve ser maior que zero.")
        return

    dados = xp_stats[user_id]
    xp_antigo = dados["xp"]
    nivel_antigo = dados["nivel"]

    xp_novo = max(0, xp_antigo - valor)  # subtração bruta e literal, só travando em 0
    nivel_novo, _, _ = _calcular_nivel(xp_novo)

    dados["xp"] = xp_novo
    dados["nivel"] = nivel_novo

    await _salvar_xp_stats()
    await _atualizar_ranking_xp()

    # Tenta identificar a pessoa pra exibir nome/menção; se não conseguir
    # (saiu do servidor, ID errado, etc.), mostra só o ID mesmo.
    membro = None
    if ctx.guild is not None:
        membro = ctx.guild.get_member(user_id)
        if membro is None:
            try:
                membro = await ctx.guild.fetch_member(user_id)
            except discord.NotFound:
                membro = None

    nome_exibicao = membro.mention if membro else f"`{user_id}`"

    aviso_nivel = (
        f" (nível caiu de `{nivel_antigo}` para `{nivel_novo}`)"
        if nivel_novo != nivel_antigo else ""
    )

    await ctx.send(
        f"📉 {nome_exibicao} perdeu **{valor}** pontos de XP — "
        f"de `{xp_antigo}` para `{xp_novo}`{aviso_nivel} — ranking já atualizado."
    )


@bot.command(name="xpdebug")
async def cmd_xp_debug(ctx):
    """Mostra dados brutos do ranking de XP pra diagnosticar problemas. Só o dono do bot pode usar."""
    if ctx.author.id != CRIADOR_ID:
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        await ctx.send("⚠️ Bot não está em nenhum servidor.")
        return

    cargo_xp = guild.get_role(CARGO_XP_ID)
    canal_xp = guild.get_channel(CANAL_XP_ID)

    linhas = [
        f"**Cargo de XP encontrado:** {'✅ sim' if cargo_xp else '❌ NÃO — verifique o ID do cargo'}",
        f"**Membros com o cargo:** {len(cargo_xp.members) if cargo_xp else 0}",
        f"**Canal de XP encontrado:** {'✅ sim' if canal_xp else '❌ NÃO — verifique o ID do canal'}",
        f"**ID da mensagem de ranking salva:** `{_xp_ranking_message_id}` (página atual: `{_xp_ranking_pagina_atual}`)",
        f"**Entradas em xp_stats (memória):** {len(xp_stats)}",
        f"**Arquivo de dados existe?** {'✅ sim' if os.path.exists(_XP_DATA_FILE) else '❌ não'}",
        "",
        "**Conteúdo bruto de xp_stats:**",
    ]
    if xp_stats:
        for uid, s in xp_stats.items():
            membro = guild.get_member(uid)
            nome = membro.display_name if membro else f"<@{uid}>"
            linhas.append(f"`{uid}` ({nome}) — {s}")
    else:
        linhas.append("*vazio — nenhuma mensagem foi registrada ainda em memória*")

    texto = "\n".join(linhas)
    if len(texto) > 1900:
        texto = texto[:1900] + "\n... (cortado)"
    await ctx.send(f"🔍 **Diagnóstico do Ranking de XP**\n{texto}")


class ReiniciarRankingView(discord.ui.View):
    """View de confirmação do reset total do ranking de interação (XP).
    Só o Reality (CRIADOR_ID) pode confirmar ou cancelar — qualquer outra
    pessoa que clicar recebe um aviso de acesso negado."""

    def __init__(self):
        super().__init__(timeout=60)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != CRIADOR_ID:
            await interaction.response.send_message(
                "👽 **Renan:** ...acesso negado. Só o Reality pode confirmar isso.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="✅ Confirmar reset",
        style=discord.ButtonStyle.danger,
        custom_id="reiniciar_ranking_confirmar"
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        global _xp_ranking_pagina_atual

        xp_stats.clear()
        _xp_ultimo_ganho.clear()
        _xp_ranking_pagina_atual = 0

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="♻️ **Ranking de interação reiniciado — todo mundo voltou a 0.**",
            embed=None,
            view=self
        )
        self.stop()

        guild = interaction.guild or (bot.guilds[0] if bot.guilds else None)
        if guild is not None:
            await _atualizar_ranking_xp()

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="reiniciar_ranking_cancelar"
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Reset cancelado.", embed=None, view=self)
        self.stop()


@bot.command(name="reiniciarranking")
async def cmd_reiniciar_ranking(ctx):
    """Reseta TODO o ranking de interação (xp, nível, criaturas, vitórias e
    derrotas) de volta a 0. Só o Reality pode usar. Uso: .reiniciarranking"""
    if ctx.author.id != CRIADOR_ID:
        return

    embed = discord.Embed(
        title="♻️ Reiniciar Ranking de Interação",
        description=(
            "Isso vai **zerar TUDO** — xp, nível, criaturas desbloqueadas, "
            "vitórias e derrotas de **todo mundo** no ranking.\n\n"
            "Tem certeza?"
        ),
        color=0xff4444
    )
    embed.set_footer(text="👽 Renan — Sistema de Nível")
    await ctx.send(embed=embed, view=ReiniciarRankingView())


class ReiniciarGeralRPGView(discord.ui.View):
    """View de confirmação do reset GERAL do RPG — a versão "nuclear" do
    .reiniciarranking: zera xp, nível, criaturas (inclusive Bestas),
    vitórias/derrotas e favorita de TODO MUNDO, e por cima disso também
    zera os boosters (Booster de Call e Booster de xp em dobro) e qualquer
    ovo incubando. Só o Reality (CRIADOR_ID) pode confirmar ou cancelar —
    qualquer outra pessoa que clicar recebe um aviso de acesso negado."""

    def __init__(self):
        super().__init__(timeout=60)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != CRIADOR_ID:
            await interaction.response.send_message(
                "👽 **Renan:** ...acesso negado. Só o Reality pode confirmar isso.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="✅ Confirmar reset geral",
        style=discord.ButtonStyle.danger,
        custom_id="reiniciar_geral_rpg_confirmar"
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        global _xp_ranking_pagina_atual

        total_pessoas = len(xp_stats)

        # 🧨 Zera TUDO do RPG, de TODO MUNDO — xp/nível/criaturas/vitórias e
        # derrotas (xp_stats), cooldown de mensagem, boosters (call e xp em
        # dobro), cooldown de desafio de batalha e ovos incubando.
        xp_stats.clear()
        _xp_ultimo_ganho.clear()
        _xp_ranking_pagina_atual = 0
        _call_booster_inicio.clear()
        _call_booster_nivel_anunciado.clear()
        _xp_booster_ate.clear()
        _batalha_ultimo_desafio.clear()
        _ovos_pendentes.clear()
        _ovos_dragao_pendentes.clear()

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=(
                "☠️♻️ **RESET GERAL DO RPG CONCLUÍDO.** Xp, nível, criaturas, "
                "vitórias/derrotas, Booster de Call, Booster de xp em dobro e "
                f"ovos incubando de **`{total_pessoas}`** pessoa(s) voltaram a "
                "**0** — do zero, pra todo mundo, sem exceção."
            ),
            embed=None,
            view=self
        )
        self.stop()

        # 💾 Persiste o reset em disco na hora — sem isso, um restart do bot
        # antes do próximo ganho de xp de alguém traria os dados antigos de
        # volta, já que cada arquivo ainda estaria com o conteúdo de antes.
        asyncio.create_task(_salvar_xp_stats())
        asyncio.create_task(_salvar_call_booster_stats())
        asyncio.create_task(_salvar_xp_booster_stats())

        guild = interaction.guild or (bot.guilds[0] if bot.guilds else None)
        if guild is not None:
            await _atualizar_ranking_xp()

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="reiniciar_geral_rpg_cancelar"
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Reset cancelado.", embed=None, view=self)
        self.stop()


@bot.command(name="reiniciogeralrpg", aliases=["resetgeralrpg"])
async def cmd_reiniciogeralrpg(ctx):
    """Reseta ABSOLUTAMENTE TUDO do RPG, de TODO MUNDO, de uma vez: xp, nível,
    criaturas desbloqueadas (inclusive Bestas), Níveis de Capacidade,
    favorita, vitórias e derrotas, Booster de Call, Booster de xp em dobro
    (baú/boss) e ovos incubando (.ovo/.ovodragao). Diferente do
    .reiniciarranking (que só zera xp/nível/criaturas), esse também zera os
    boosters e já salva o reset em disco na hora. Irreversível. Só o Reality
    pode usar. Uso: .reiniciogeralrpg"""
    if ctx.author.id != CRIADOR_ID:
        return

    total_pessoas = len(xp_stats)

    embed = discord.Embed(
        title="☠️♻️ Reset GERAL do RPG",
        description=(
            f"Isso vai **zerar ABSOLUTAMENTE TUDO** de **`{total_pessoas}`** pessoa(s) "
            "que já têm dados no ranking:\n\n"
            "• XP e nível\n"
            "• Criaturas desbloqueadas (inclusive 🐺 Bestas) e Níveis de Capacidade\n"
            "• Criatura favorita\n"
            "• Vitórias e derrotas\n"
            "• 🔥 Booster de Call (streak) de todo mundo\n"
            "• ⚡ Booster de xp em dobro (baú/boss) de todo mundo\n"
            "• 🥚 Ovos incubando (`.ovo` e `.ovodragao`)\n\n"
            "⚠️ **Isso é irreversível e vale pra TODO MUNDO, sem exceção.**\n\n"
            "Tem certeza?"
        ),
        color=0xff0000
    )
    embed.set_footer(text="👽 Renan — Sistema de Nível")
    await ctx.send(embed=embed, view=ReiniciarGeralRPGView())


@bot.command(name="xpbackfill")
async def cmd_xp_backfill(ctx, limite: int = None):
    """Varre o histórico dos 3 canais de ranking e marca como 'elegivel' todo
    mundo que JÁ mandou mensagem lá antes — inclusive mensagens antigas, de
    antes da liberação do cargo. Sem isso, só quem mandar uma mensagem NOVA
    depois da atualização apareceria no ranking; com isso, quem já participava
    antes aparece de uma vez, sem precisar mandar mensagem de novo.
    Só o dono do bot pode usar. Uso: .xpbackfill [limite de msgs por canal]"""
    if ctx.author.id != CRIADOR_ID:
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        await ctx.send("⚠️ Bot não está em nenhum servidor.")
        return

    aviso = await ctx.send(
        "🔎 Varrendo o histórico dos canais de ranking pra achar quem já "
        "participou antes... isso pode levar um tempinho em canais grandes."
    )

    encontrados = set()
    for canal_id in _XP_CANAIS_RANKING:
        canal = guild.get_channel(canal_id)
        if canal is None:
            continue
        try:
            async for msg in canal.history(limit=limite):
                if msg.author.bot:
                    continue
                encontrados.add(msg.author.id)
        except (discord.Forbidden, discord.HTTPException) as e:
            await ctx.send(f"⚠️ Não consegui ler o histórico de {canal.mention}: `{e}`")

    novos = 0
    for uid in encontrados:
        membro = guild.get_member(uid)
        if membro is None:
            continue  # já saiu do servidor — não destrava quem não tá mais aqui
        dados = xp_stats[uid]
        if not dados.get("elegivel"):
            novos += 1
        dados["elegivel"] = True

    await _salvar_xp_stats()
    await _atualizar_ranking_xp()

    await aviso.edit(
        content=(
            f"✅ Varredura concluída! `{len(encontrados)}` pessoas encontradas nos canais de ranking, "
            f"`{novos}` delas foram destravadas agora e já aparecem no ranking fixo."
        )
    )


# Carrega o histórico de XP salvo assim que o módulo sobe — antes mesmo de conectar no Discord
_carregar_xp_stats()

# Carrega a streak salva do Booster de Call — a reconciliação final (quem
# realmente ainda está numa call válida) acontece no on_ready.
_carregar_call_booster_stats()

# ══════════════════════════════════════════════════════════════════════
# BATALHA DE CRIATURAS — "Eu te desafio @alguém"
# Quando alguém escreve "eu te desafio @pessoa" no chat, o Renan
# armam uma batalha dramática entre duas criaturas sorteadas aleatoriamente
# — uma pro desafiante, outra pro desafiado. No fim, quem vence PODE roubar
# uma fatia do XP total de quem perdeu (no ranking de nível): é lançado um
# "dado" que decide entre 1% e 20%... ou, com uma certa chance, nada.
# ══════════════════════════════════════════════════════════════════════

# ── Raridades das criaturas ──────────────────────────────────────────────
# Define o emoji/cor/label de cada raridade e o PESO usado no sorteio de
# batalha (quanto maior o peso, mais fácil essa raridade aparecer). Isso faz
# criaturas Lendárias serem naturalmente mais raras de invocar (e, por
# tabela, mais raras de desbloquear).
_RARIDADES = {
    "comum":    {"label": "Comum",    "emoji": "⚪", "cor": 0xb0b0b0, "peso": 50},
    "raro":     {"label": "Raro",     "emoji": "🔵", "cor": 0x3498db, "peso": 25},
    "epico":    {"label": "Épico",    "emoji": "🟣", "cor": 0x9b59b6, "peso": 15},
    "lendario": {"label": "Lendário", "emoji": "🟡", "cor": 0xf1c40f, "peso": 10},
    # 🌀 Elementais: mais fortes que as Lendárias, mas ainda um degrau abaixo
    # das Bestas — o resto das raridades acima delas (Bestas, Fósseis,
    # Secretas, Míticas) elas não chegam a bater de frente com tanta força.
    # Não entram no sorteio normal de recompensa nem no 🪙 Baú/.ovo — a ÚNICA
    # forma de conseguir um é levando uma criatura 🟣 Épica até o Nível de
    # Capacidade 6 (ver _ELEMENTAL_NIVEL_DESBLOQUEIO e
    # _checar_desbloqueio_elemental, mais abaixo): ao bater esse nível, a
    # pessoa recebe automaticamente, de graça, 1 Elemental ALEATÓRIO dentre
    # os que ainda não tiver. Além disso, todo Elemental USADO numa batalha
    # (convocado, ganhando ou perdendo — não importa) já concede na hora,
    # pra quem o usou, um Booster de xp em dobro por
    # _ELEMENTAL_BOOSTER_MINUTOS minutos (ver _executar_batalha).
    "elemental": {"label": "Elemental", "emoji": "🌀", "cor": 0xe67e22, "peso": 7},
    # 🐺 Bestas: mais fortes que as Lendárias, mas ainda um degrau abaixo das
    # Secretas. Não entram no sorteio normal de recompensa nem no 🪙 Baú — a
    # ÚNICA forma de conseguir uma é levando uma criatura Comum, Rara,
    # Épica ou Lendária até o Nível de Capacidade máximo (ver _BESTAS_POR_TIER e
    # _checar_desbloqueio_besta, mais abaixo). O peso aqui só importa pra
    # decidir a chance dela ser invocada em batalha depois de já ter sido
    # conquistada.
    "bestas":   {"label": "Besta",    "emoji": "🐺", "cor": 0x922b21, "peso": 6},
    # 🦴 Fósseis: um degrau abaixo das Secretas, mas mais fortes que as
    # Lendárias — ver a lógica de desbloqueio própria delas mais abaixo
    # (_FOSSIL_CHANCE_DESBLOQUEIO), gatilhada só quando os dois lados de uma
    # batalha estão numa call de voz.
    "fosseis":  {"label": "Fóssil",   "emoji": "🦴", "cor": 0xc2a878, "peso": 3},
    "secreto":  {"label": "Secreto",  "emoji": "🌌", "cor": 0x6c2eb5, "peso": 2},
    "mitico":   {"label": "Mítico",   "emoji": "🐉", "cor": 0xe0115f, "peso": 5},
}
_ORDEM_RARIDADES = ("mitico", "secreto", "fosseis", "bestas", "elemental", "lendario", "epico", "raro", "comum")  # do mais raro pro mais comum, pra exibição

# Cada criatura tem um "id" fixo (usado para salvar quem já desbloqueou),
# um "nome" de exibição, o "gif" e a "raridade" (chave de _RARIDADES).
_BATALHA_CRIATURAS = [
    # ── Comuns ──────────────────────────────────────────────────────────
    {"id": "caveira_perpetua",        "nome": "Caveira Perpétua",             "raridade": "comum",    "gif": "https://i.pinimg.com/originals/11/d4/f6/11d4f665781ad7710f79e76ae03532bf.gif"},
    {"id": "samurai_pix",             "nome": "Samurai do Pix",               "raridade": "comum",    "gif": "https://i.pinimg.com/originals/32/e6/fe/32e6fe1d93519ce4ed0c9d1ef666ea86.gif"},
    {"id": "abandonado",              "nome": "O Abandonado",                 "raridade": "comum",    "gif": "https://i.pinimg.com/originals/19/7b/88/197b887956c1741536cbda7a8bf0c59c.gif"},
    {"id": "desconectado",            "nome": "O Desconectado",               "raridade": "comum",    "gif": "https://64.media.tumblr.com/e59c49cc960b3af010126aa2185f9af4/tumblr_o2ukydWovF1rznluto3_250.gif"},
    {"id": "rino_acabado",            "nome": "Rino, o Acabado",              "raridade": "comum",    "gif": "https://33.media.tumblr.com/fc4838c3660618bf7dd87103de60871b/tumblr_inline_nzsz2t9ltH1s38bty_500.gif"},
    {"id": "plebeu",                  "nome": "O Plebeu",                     "raridade": "comum",    "gif": "https://i.pinimg.com/originals/1c/9f/2b/1c9f2b392f039b76b7f3a68039730d21.gif"},
    {"id": "bandido",                 "nome": "Bandido",                      "raridade": "comum",    "gif": "https://cdnb.artstation.com/p/assets/images/images/050/343/519/original/rafael-francoi-neutral-inxikrahsoldier-preview.gif?1654628639"},
    {"id": "ranfroi_ultimo_plebeu",    "nome": "Ranfroi, o Último Plebeu",     "raridade": "comum",    "gif": "https://cdna.artstation.com/p/assets/images/images/050/342/714/original/rafael-francoi-mk2.gif?1654627365"},
    {"id": "buzzmole_eletrico",        "nome": "Buzzmole Elétrico do Eco",     "raridade": "comum",    "gif": "https://www.natekling.com/uploads/8/2/3/8/8238935/7185980.gif"},
    {"id": "blindado_metaltooth",      "nome": "O Blindado",                   "raridade": "comum",    "gif": "https://cdna.artstation.com/p/assets/images/images/050/342/682/original/rafael-francoi-metaltooth.gif?1654627258"},
    {"id": "cueio_pistola",            "nome": "Cueio Pistola",                "raridade": "comum",    "gif": "https://i.pinimg.com/originals/8c/d8/9c/8cd89c36fdb3215e7b7f82a8e94605d2.gif"},

    # ── Raras ───────────────────────────────────────────────────────────
    {"id": "cavaleiro_elemental",     "nome": "Cavaleiro Elemental",          "raridade": "raro",     "gif": "https://i.pinimg.com/originals/f0/6a/a4/f06aa45318cce9f16f2b3e591a138ae1.gif"},
    {"id": "caveira_prisao",          "nome": "Caveira da Prisão",            "raridade": "raro",     "gif": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEivaQ2fr4t0qnYKfUiXbCeBU2HGF2vMB6oCjiEbAjADBdNYPoOqzEU8jSDdHDwD5xgI7MGL9qj0eH60EgBEaGjgV4JIHDait9dSFusVjLvykhwIWHPa4tfeDhzOr3uhwQfyNtzw7mz-Q9_E/s1600/Phantasm_attack_8.gif"},
    {"id": "eco_luz",                 "nome": "Eco da Luz",                   "raridade": "raro",     "gif": "https://i.pinimg.com/originals/25/83/b2/2583b2768cb33f0165e3a88ac3debbde.gif"},
    {"id": "cientista_louco",         "nome": "Cientista Louco",              "raridade": "raro",     "gif": "https://i.pinimg.com/originals/f7/45/05/f74505bee8fec82f0eb6e925c61b35f2.gif"},
    {"id": "brutal",                  "nome": "O Brutal",                     "raridade": "raro",     "gif": "https://i.pinimg.com/originals/fd/1f/8a/fd1f8aa84a2d1b1d1486c68613216d9d.gif"},
    {"id": "cavaleiro_sinistro",      "nome": "Cavaleiro do Sinistro",        "raridade": "raro",     "gif": "https://i.pinimg.com/originals/1c/3a/9b/1c3a9bc1c91135ff036d1d168d15e474.gif"},
    {"id": "kreging",                 "nome": "Kreging",                      "raridade": "raro",     "gif": "https://64.media.tumblr.com/3211afe2da2effd51671993d42cecc81/tumblr_oomh73qHh21qciqqno5_250.gif"},
    {"id": "besta_gelida",             "nome": "Besta Gélida",                 "raridade": "raro",     "gif": "https://i.pinimg.com/originals/a6/a7/14/a6a714c4caab8f29b00e36feecc37fc2.gif"},
    {"id": "pai_da_sorte",             "nome": "O Pai da Sorte",               "raridade": "raro",     "gif": "https://i.redd.it/9w2ulp6ym1ky.gif"},
    {"id": "besta_do_eco",             "nome": "A Besta do Eco",               "raridade": "raro",     "gif": "https://i.pinimg.com/originals/a2/14/20/a214205173961824624e41024b6c5fdd.gif"},
    {"id": "ravok_submetido_eco",      "nome": "Ravok, o Submetido do Eco",    "raridade": "raro",     "gif": "https://i.pinimg.com/originals/a7/ed/26/a7ed267e84861ec466c82095bb0bad63.gif"},
    {"id": "yamikiba",                 "nome": "Yamikiba",                     "raridade": "raro",     "gif": "https://cdnb.artstation.com/p/assets/images/images/050/343/457/original/rafael-francoi-neutral-inxikrahbuilder-preview.gif?1654628532"},

    # ── Épicas ──────────────────────────────────────────────────────────
    {"id": "heroina_esmeraldas",      "nome": "Heroína das Esmeraldas",       "raridade": "epico",    "gif": "https://i.pinimg.com/originals/40/4f/d9/404fd93484c2592c78a13cf25891c156.gif"},
    {"id": "robin_dourado",           "nome": "Robin Dourado",                "raridade": "epico",    "gif": "https://i.pinimg.com/originals/fc/26/21/fc26214b7e21990e483df07f8ee616e8.gif"},
    {"id": "buda_eco",                "nome": "Buda do Eco",                  "raridade": "epico",    "gif": "https://i.pinimg.com/originals/de/cc/64/decc640148693d24cbccfce9262d16ae.gif"},
    {"id": "monstro_portao",          "nome": "O Monstro do Portão",          "raridade": "epico",    "gif": "https://i.pinimg.com/originals/1f/4a/d7/1f4ad7fd9917093bc7463394497fd920.gif"},
    {"id": "ultimo_atlanta",          "nome": "Último de Atlanta",            "raridade": "epico",    "gif": "https://i.pinimg.com/originals/84/a6/8b/84a68ba244c9034c52dcb8002f90a87f.gif"},
    {"id": "guerreiro_trovao",        "nome": "Guerreiro do Trovão",          "raridade": "epico",    "gif": "https://i.pinimg.com/originals/6b/2c/21/6b2c2173d12ddf1f2adae8f0064f772d.gif"},
    {"id": "anti_elemento",           "nome": "O Anti-Elemento",              "raridade": "epico",    "gif": "https://i.pinimg.com/originals/d1/ee/0e/d1ee0eed40bd9a2052e4b0ce55e741d9.gif"},
    {"id": "vortex",                  "nome": "O Vórtex",                     "raridade": "epico",    "gif": "https://cdnb.artstation.com/p/assets/images/images/050/342/679/original/rafael-francoi-build-epic-01.gif?1654627256"},
    {"id": "seraphine_guerreira",      "nome": "Seraphine, a Guerreira",       "raridade": "epico",    "gif": "https://i.pinimg.com/originals/15/de/fc/15defcb5f35239554da784918902b32a.gif"},
    {"id": "corrompido",               "nome": "O Corrompido",                 "raridade": "epico",    "gif": "https://cdnb.artstation.com/p/assets/images/images/050/343/359/original/rafael-francoi-f2-boss-preview.gif?1654628376"},
    {"id": "ignara_musa_chamas",       "nome": "Ignara, a Musa das Chamas",    "raridade": "epico",    "gif": "https://i.pinimg.com/originals/01/a0/f0/01a0f071ff7c66dab9de366c4c8da0bf.gif"},
    {"id": "primeiro_graking",         "nome": "O Primeiro Graking",           "raridade": "epico",    "gif": "https://i.pinimg.com/originals/c1/18/60/c11860b4b9e9b179b1b8dbc2ce640839.gif"},
    {"id": "ophryx_dama_besta",        "nome": "Ophryx, a Dama e a Besta",     "raridade": "epico",    "gif": "https://gd-hbimg.huaban.com/bbf9f681a72dc53b226e1efe204770da4f98adf250494-5EKNdd_fw658"},
    {"id": "warden_eco",               "nome": "Warden do Eco",                "raridade": "epico",    "gif": "https://cdna.artstation.com/p/assets/images/images/050/343/624/original/rafael-francoi-ynuyt-unleashed.gif?1654628832"},
    {"id": "kurojin",                  "nome": "Kurojin",                      "raridade": "epico",    "gif": "https://cdnb.artstation.com/p/assets/images/images/050/343/359/original/rafael-francoi-f2-boss-preview.gif?1654628376"},
    {"id": "xalkuro",                  "nome": "Xal'Kuro",                     "raridade": "epico",    "gif": "https://i.redd.it/sifc575zp2dy.gif"},
    {"id": "salafrario",               "nome": "O Salafrário",                 "raridade": "epico",    "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531101852752416848/1785113407534.gif?ex=6a67fd38&is=6a66abb8&hm=631b4328a747f1527a2a2e440694c136d28683eb7ef0dc46e17322d779178db4&"},

    # ── Lendárias ───────────────────────────────────────────────────────
    {"id": "ultimo_guerreiro",        "nome": "O Último Guerreiro",           "raridade": "lendario", "gif": "https://gd-hbimg.huaban.com/da5bb9cc8fab68c2c3cabe68a7cc7a10cd277939be96-bBi4DQ"},
    {"id": "lyria_governante",        "nome": "Lyria, a Governante",          "raridade": "lendario", "gif": "https://i.pinimg.com/originals/9e/88/99/9e88991126a8bdd32a89e43ae683f3b4.gif"},
    {"id": "kaiju_eco",               "nome": "Kaiju do Eco",                 "raridade": "lendario", "gif": "https://i.pinimg.com/originals/02/ef/09/02ef09d38f7435de3a2e8d26508a17ec.gif"},
    {"id": "protetor_portao_inferno", "nome": "Protetor do Portão do Inferno","raridade": "lendario", "gif": "https://i.pinimg.com/originals/6d/bc/58/6dbc588871368635891ea6a5f12d3cf2.gif"},
    {"id": "magmata",                 "nome": "O Magmata",                    "raridade": "lendario", "gif": "https://i.redd.it/0jk54f0ocjwy.gif"},
    {"id": "vreg_entre_mundos",       "nome": "Vreg, Entre Mundos",           "raridade": "lendario", "gif": "https://cdna.artstation.com/p/assets/images/images/050/343/134/original/rafael-francoi-boss-f4-preview.gif?1654628012"},
    {"id": "azrakiel_monarca",        "nome": "Azrakiel, o Monarca",          "raridade": "lendario", "gif": "https://i.pinimg.com/originals/a3/20/90/a32090812f05b6ac55c66e2cbf5c5621.gif"},
    {"id": "arkanis_primeiro_reis",   "nome": "Arkanis, o Primeiro dos Reis", "raridade": "lendario", "gif": "https://i.pinimg.com/originals/d5/66/4e/d5664e6db68e21ae002431b9fd13ed2d.gif"},
    {"id": "auremortis_guardia_almas","nome": "Auremortis, a Guardiã das Almas Perdidas", "raridade": "lendario", "gif": "https://i.redd.it/nij0nx9bnkpy.gif"},
    {"id": "goldryn_chama_destino",   "nome": "Goldryn, a Chama Que Consome o Destino",   "raridade": "lendario", "gif": "https://i.redd.it/go2trcn2yoby.gif"},
    {"id": "thanarion_arauto_fim",    "nome": "Thanarion, o Arauto do Fim",   "raridade": "lendario", "gif": "https://i.pinimg.com/originals/04/96/7c/04967c814e98570fbffe8329fe36d2bc.gif"},
    {"id": "nythrax_senhor_sombras",  "nome": "Nythrax, o Senhor das Sombras","raridade": "lendario", "gif": "https://cdnb.artstation.com/p/assets/images/images/050/342/691/original/rafael-francoi-exotic-spellcaster.gif?1654627313"},
    {"id": "umbrael_observa_alem",    "nome": "Umbrael, o Que Observa Além",  "raridade": "lendario", "gif": "https://gd-hbimg.huaban.com/9064a16a34ed6e88bab3dc8c3815a6258b1d16c54068a-6KOtGT_fw658"},
    {"id": "noxar_puro_trovao",       "nome": "Noxar, o Puro Trovão",         "raridade": "lendario", "gif": "https://i.pinimg.com/originals/c7/6c/87/c76c873ca7d63b7fb29792ad26d36368.gif"},
    {"id": "malgorath_ultima_raca",   "nome": "Malgorath, o Último de Sua Raça", "raridade": "lendario", "gif": "https://i.pinimg.com/originals/df/a8/fc/dfa8fca7813bbb3e42613523c2e2ba43.gif"},
    {"id": "jigokuken",               "nome": "Jigokuken",                    "raridade": "lendario", "gif": "https://i.pinimg.com/originals/6e/a3/b3/6ea3b3d49760fab3d42b0570f1f9e69a.gif"},
    {"id": "raiketsu_lamina_dourada", "nome": "Raiketsu, a Lâmina Dourada",   "raridade": "lendario", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531098422952726758/1785112683012.gif?ex=6a67fa06&is=6a66a886&hm=4b58d4ae7eb0fc825c630d44cd22ac4b017c1a78f8881e7b3e6af06ab7adea7a"},

    # ── Elementais ──────────────────────────────────────────────────────
    # Destravados por CONQUISTA, não por sorteio — mais fortes que as
    # Lendárias, mas ainda um degrau abaixo das Bestas. A única forma de
    # conseguir um é levando uma criatura 🟣 Épica até o Nível de Capacidade
    # 6 (veja _ELEMENTAL_NIVEL_DESBLOQUEIO e _checar_desbloqueio_elemental,
    # mais abaixo) — é sempre um Elemental ALEATÓRIO dentre os que a pessoa
    # ainda não tem. Todo Elemental USADO numa batalha (ganhando ou
    # perdendo, não importa) também concede na hora um Booster de xp em
    # dobro por _ELEMENTAL_BOOSTER_MINUTOS minutos pra quem o convocou.
    {"id": "ignar_senhor_chamas",      "nome": "Ignar, o Senhor das Chamas Eternas", "raridade": "elemental", "gif": "https://images.cara.app/production/posts/87424233-d5f7-43cd-988b-5e1b151d4835/sunpixels-AoOvOaapYAziRLRy67LQ6-firee.gif?width=750&quality=100"},
    {"id": "zephros_soberano_ventos",  "nome": "Zephros, o Soberano dos Ventos",     "raridade": "elemental", "gif": "https://images.cara.app/production/posts/aa3523f4-44cd-4f6f-99eb-3819331ead94/sunpixels-0VDPXm8ZraKByQgekVp0J-air.gif?width=750&quality=100"},
    {"id": "granor_colosso_pedra",     "nome": "Granor, o Colosso de Pedra",         "raridade": "elemental", "gif": "https://images.cara.app/production/posts/8acf2d4e-77c7-4c20-a674-7cd29d623659/sunpixels-Mj80n0EV-_lHz9IbhkoFP-gf.gif?width=750&quality=100"},
    {"id": "pyroth_devorador_vulcoes", "nome": "Pyroth, o Devorador de Vulcões",     "raridade": "elemental", "gif": "https://images.cara.app/production/posts/a38409ff-ef92-4890-a848-93c23b4233ad/sunpixels-sIGdQ9FU-zs5U1MeFpcE5-eeasd.gif?width=750&quality=100"},
    {"id": "sylvara_guardia_floresta", "nome": "Sylvara, a Guardiã da Floresta Ancestral", "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531800568241197147/1785280104128.gif?ex=6a6a87f2&is=6a693672&hm=ab516e494a292d2013a33f5afa07c486bb99ecc7fbddd999310c7b33b401b47a"},
    {"id": "nereia_rainha_mares",      "nome": "Nereia, a Rainha das Marés",         "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531800691901730886/1785280137642.gif?ex=6a6a8810&is=6a693690&hm=cf17a7d242a0f5763f6ff2ea4d89ba25f9d6abcd7e210f0fb27915feb37f9216"},
    {"id": "lumiel_arauto_aurora",     "nome": "Lumiel, o Arauto da Aurora",         "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531800926137090208/1785280195193.gif?ex=6a6a8848&is=6a6936c8&hm=a37ea0db0607dfdd33dd72b7344576024d2ba814d8e1c5646ebb22a34a66ae88"},
    {"id": "nocthar_monarca_sombras",  "nome": "Nocthar, o Monarca das Sombras",     "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531801365662404678/1785280298784.gif?ex=6a6a88b1&is=6a693731&hm=9f7e3de1c1ee64e62d615afd557e3480ea59da248a8477c2648f37af011c55de"},
    {"id": "zephor_portador_raios",    "nome": "Zephor, o Portador dos Raios",       "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531801627856470118/1785280362728.gif?ex=6a6a88ef&is=6a69376f&hm=241d97ed04603d1cd85cf5bf624b83fef20510ab79e2a07da78e46ae49c7788a"},
    {"id": "venyx_portador_praga",     "nome": "Venyx, o Portador da Praga",         "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531801741555929218/1785280389431.gif?ex=6a6a890a&is=6a69378a&hm=95d8b56837124085b7c9707af19ef88e86b4ecd6232149784e6674ec86d304b3"},
    {"id": "mordrak_coracao_carmesim", "nome": "Mordrak, o Coração Carmesim",        "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531801803476439060/1785280404640.gif?ex=6a6a8919&is=6a693799&hm=2debab6eaa3de2c58a7145e33628198930e778414a2409bac1eac48a5ca754cb"},
    {"id": "gravion_mestre_gravidade", "nome": "Gravion, o Mestre da Gravidade",     "raridade": "elemental", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531802763376201920/1785280632048.gif?ex=6a6a89fe&is=6a69387e&hm=7e98df335f73559ff1fe2c4775d4ab74ab7360d5912e40f764b3b9a977df0e1c"},

    # ── Bestas ──────────────────────────────────────────────────────────
    # Mais fortes que as Lendárias, mas ainda um degrau abaixo das Secretas.
    # Nunca saem de sorteio de vitória nem do 🪙 Baú — a ÚNICA forma de
    # conseguir uma é levando uma criatura Comum, Rara, Épica ou Lendária até
    # o Nível de Capacidade máximo (veja _BESTAS_POR_TIER logo abaixo, que
    # define qual "tier" desbloqueia qual Besta):
    #   ⚪ Comum    no Nível máximo → sorteia 1 entre Kragor / Espinho Maldito
    #   🔵 Raro     no Nível máximo → sorteia 1 entre Drogan / A Matriarca do Abismo
    #   🟣 Épico    no Nível máximo → concede Venomor
    #   🟡 Lendário no Nível máximo → concede O Último Shogun das Trevas
    {"id": "kragor_senhor_presas",    "nome": "Kragor, Senhor das Presas",     "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530616424576323615/1784997759114.gif?ex=6a663921&is=6a64e7a1&hm=ce8f0e4db85718ec33963682c0cf21136ce59d18b1dfa4861bf64716f9b802c4"},
    {"id": "espinho_maldito",         "nome": "Espinho Maldito",               "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530620836648849519/1784998710439.gif?ex=6a663d3d&is=6a64ebbd&hm=fccdd2a51553437b3244b38e95abec8d7eb2c753a575be68c3c5468a01256fce"},
    {"id": "drogan_carniceiro",       "nome": "Drogan, o Carniceiro",          "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530620836187345046/1784998831160.gif?ex=6a663d3c&is=6a64ebbc&hm=a55e419e47578dc873b7ab25687d4a14d994aa29d954012dd53afba93331834c"},
    {"id": "matriarca_abismo",        "nome": "A Matriarca do Abismo",         "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530621862898438184/1784999080550.gif?ex=6a663e31&is=6a64ecb1&hm=fb9e9ae76d5a675e227bbc929fa5028b415d196abe9c07dc4513c5483f091a45"},
    {"id": "venomor",                 "nome": "Venomor",                       "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530626370051506216/1785000151649.gif?ex=6a664264&is=6a64f0e4&hm=19fd34a9f84377e2b4c3e77b6c57d94ca043d394eb261b834ac2cff5b8f374b0"},
    {"id": "ultimo_shogun_trevas",    "nome": "O Último Shogun das Trevas",    "raridade": "bestas",   "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531101852417003722/1785113506856.gif?ex=6a67fd38&is=6a66abb8&hm=28a407b40c11ddc85ead690da23b6275e8bbcf6502b8f846ae62da026e5910be&"},

    # ── Fósseis ─────────────────────────────────────────────────────────
    # Um degrau abaixo das Secretas, mas mais fortes que as Lendárias. Não
    # entram no sorteio normal de recompensa nem no 🪙 Baú/.ovo — a ÚNICA
    # forma de conseguir uma é vencendo uma batalha de "eu te desafio" com
    # os DOIS lados (desafiante e desafiado) numa call de voz no momento:
    # aí sim rola uma chance de _FOSSIL_CHANCE_DESBLOQUEIO de o vencedor
    # desenterrar um Fóssil novo (ver _executar_batalha, mais abaixo).
    {"id": "kharox",                  "nome": "Kharox",                        "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/39675b30-c22a-4fee-9169-796d8df605c3/sovanjedi-QxpAB2XnRkgnAb8AG_sZT-jho_4x.gif?width=1920"},
    {"id": "tyrgath",                 "nome": "Tyrgath",                       "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/39675b30-c22a-4fee-9169-796d8df605c3/sovanjedi-_Zu5_q0u8pF02EL_xZ-di-goremagala_4x.gif?width=1920"},
    {"id": "fossorak",                "nome": "Fossorak",                      "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/39675b30-c22a-4fee-9169-796d8df605c3/sovanjedi-Erok4gaSmAq53n-OFHmo7-barioth_4x.gif?width=1920"},
    {"id": "rexolith",                "nome": "Rexolith",                      "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/e5cf266b-89a9-4f7d-b581-9adc6e1bc374/sovanjedi-yORqbtobG_AsZfkJjT7qL-zin_4x.gif?width=1920"},
    {"id": "titanclaw",               "nome": "Titanclaw",                     "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/365c202e-1fc3-4676-93fa-ff982bc10652/sovanjedi-u6eIN5WKwTqaZt2wt8WJl-magna_4x.gif?width=1920"},
    {"id": "skullmaw",                "nome": "Skullmaw",                      "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/365c202e-1fc3-4676-93fa-ff982bc10652/sovanjedi-GQrOL3cptWN7yFxDRmhMW-khezu_4x.gif?width=1920"},
    {"id": "paleotyr",                "nome": "Paleotyr",                      "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/abae2a03-07c5-42ac-b5c0-59dd1cd60907/sovanjedi-8vvofnFCout2lpQqfWKuv-NorthernMountain_idle.gif?width=750&quality=100"},
    {"id": "ossaraith",                "nome": "Ossaraith",                     "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/365c202e-1fc3-4676-93fa-ff982bc10652/sovanjedi-EjBUt_WUHgQhErjz52ysz-goss_4x.gif?width=750&quality=100"},
    {"id": "necrolith",               "nome": "Necrolith",                     "raridade": "fosseis",  "gif": "https://images.cara.app/production/posts/5e343483-c057-4aa8-a379-c27c02fd22d5/sovanjedi-ICTTsVYhJNyqg7CjKSeeQ-danaumus_TWEAKS_x4.gif?width=1920"},

    # ── Secretas ────────────────────────────────────────────────────────
    # Um degrau abaixo das Míticas, mas acima das Lendárias — e MUITO mais
    # raras de conseguir que qualquer uma delas. Só saem do 🪙 Baú (.bau),
    # com uma chance minúscula (_BAU_CHANCE_SECRETO) — nunca aparecem como
    # recompensa normal de vitória em batalha nem no .ovo.
    {"id": "nyxalith_dragao_eclipse_contaminado", "nome": "Nyxalith, o Dragão do Eclipse Contaminado", "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530548540453949492/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte8-ezgif.com-video-to-gif-converter.gif?ex=6a65f9e8&is=6a64a868&hm=520ea2ec3119628ee31e2fcdc0ffec3cd2f58abeb1299853fe6bfbfa0225dc24"},
    {"id": "magnus_frostbane",                    "nome": "Magnus Frostbane",                             "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530551857657811144/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte12-ezgif.com-video-to-gif-converter.gif?ex=6a65fcff&is=6a64ab7f&hm=b17f232f526747a90194d31ac0043cb30c66511a1df23b2ea54c79d98c633e19"},
    {"id": "drakonis_prime",                      "nome": "Drakonis Prime",                               "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530550661341646929/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte10-ezgif.com-video-to-gif-converter.gif?ex=6a65fbe1&is=6a64aa61&hm=56b3b0869302c0a49246ec7ba92b17ab28db532828585b57d68ceee9eec47c4d"},
    {"id": "pirikita",                            "nome": "Pirikita",                                     "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530543477765570590/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte6-ezgif.com-video-to-gif-converter.gif?ex=6a65f531&is=6a64a3b1&hm=95e9447603d93ff32e57592230af53ec07567d79ed1eaa5e4b886c2acc67653b"},
    {"id": "solarius_guardiao_ordem",              "nome": "Solarius, Guardião da Ordem",                  "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530556148976193636/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte14-ezgif.com-video-to-gif-converter.gif?ex=6a6600fe&is=6a64af7e&hm=5a60dce14b09c13ee02ae437cf01492ed8b8444978fa8d044efc78fff056c262"},
    {"id": "vorakthul",                            "nome": "Vorak'thul",                                   "raridade": "secreto", "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1530543478193520791/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte5-ezgif.com-video-to-gif-converter.gif?ex=6a65f531&is=6a64a3b1&hm=72a2e23365092d97d2fb9e4c23765cc0ee32765fe092f5ebb1d8bb348283d98c"},

    # ── Míticas ─────────────────────────────────────────────────────────
    # Dragões. Não entram no sorteio normal de recompensa (esse é o pool
    # de _nao_possuidas em _executar_batalha, que já os exclui) — só saem
    # pelo desbloqueio especial a cada _MITICO_VITORIAS_INTERVALO vitórias,
    # com _MITICO_CHANCE_DESBLOQUEIO de chance. Em batalha, seguem a
    # hierarquia de força das raridades (_chance_vitoria_por_raridade): são
    # a raridade mais forte de todas, mas o adversário sempre mantém uma
    # chance mínima de dar a zebra; Mítico contra Mítico é sorteio puro (50/50).
    {"id": "dragao_mar",              "nome": "Dragão do Mar",                 "raridade": "mitico",   "gif": "https://i.pinimg.com/originals/03/80/19/0380195ac5aa62eca14b4361eb30189e.gif"},
    {"id": "dragao_oriente",          "nome": "Dragão do Oriente",             "raridade": "mitico",   "gif": "https://i.pinimg.com/originals/62/9e/1f/629e1fd48d0176d8fb7bf77714387ee4.gif"},
    {"id": "dragao_caos",             "nome": "Dragão do Caos",                "raridade": "mitico",   "gif": "https://media.tenor.com/KvbrKEFBVncAAAAM/monseter-hunter.gif"},
    {"id": "dragao_prisma",           "nome": "Dragão de Prisma",              "raridade": "mitico",   "gif": "https://cdn.weasyl.com/static/media/06/de/94/06de947946dab12a282995a2535af120b36450e6bc7f8b652ac5970277647027.gif"},
    {"id": "dragao_serpente",         "nome": "Dragão Serpente",               "raridade": "mitico",   "gif": "https://cdnb.artstation.com/p/assets/images/images/039/804/307/original/camila-xiao-tokens-of-natura-sea-dragon-pixel-art-creature-for-game-card-pixel-artist-2x.gif?1626976782"},
    {"id": "dragao_aco",              "nome": "Dragão de Aço",                 "raridade": "mitico",   "gif": "https://i.pinimg.com/originals/a6/5a/41/a65a41bea0d8cac396f6309bdcb7408c.gif"},
    {"id": "dragao_ilusao",           "nome": "Dragão da Ilusão",              "raridade": "mitico",   "gif": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSIGoiDbh34-18M4L2FNgcAeTs_5ZhRrh6RwD1OevEFRg&s=10"},
    {"id": "dragao_harpia",           "nome": "Dragão Harpia",                 "raridade": "mitico",   "gif": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSac9SxVwY95I-M4FAiSTIfyflL3HKOewRthGaww-BcVQ&s=10"},
    {"id": "dragao_cavernas",         "nome": "Dragão das Cavernas",           "raridade": "mitico",   "gif": "https://64.media.tumblr.com/68dc30d0eb6ff98966ce3e03a2d7d8cc/tumblr_nzuesoPOWL1qciqqno5_540.gif"},
]

def _garantir_criaturas_iniciais(user_id: int) -> list:
    """Garante que a pessoa tenha ao menos as criaturas ⚪ Comuns já
    desbloqueadas — é o "kit inicial" de todo mundo, pra sempre ter algo
    pra invocar numa batalha mesmo antes de vencer a primeira vez.
    Só concede na primeira vez (lista vazia); depois disso o progresso
    (raras, épicas, lendárias) fica só por conta de vitórias."""
    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    dados.setdefault("usos_criaturas", {})
    if not dados["criaturas"]:
        dados["criaturas"] = [c["id"] for c in _BATALHA_CRIATURAS if c["raridade"] == "comum"]
    return dados["criaturas"]


# Detecta a frase em qualquer lugar da mensagem (com ou sem acento), desde
# que tenha alguém mencionado junto.
_BATALHA_REGEX = re.compile(r"eu\s+te\s+desaf", re.IGNORECASE)

_BATALHA_COOLDOWN_SEGUNDOS = 120    # tempo mínimo entre desafios lançados pela MESMA pessoa
_batalha_ultimo_desafio: dict = {}  # user_id -> time.time() do último desafio lançado
_batalha_canal_ativo: set = set()   # channel_id -> impede 2 batalhas rolando ao mesmo tempo no mesmo canal

_BATALHA_CHANCE_SEM_ROUBO = 0.15    # 15% de chance do vencedor não levar XP NENHUM
_BATALHA_ROUBO_MIN = 0.01           # 1%  — mínimo que o dado pode sortear
_BATALHA_ROUBO_MAX = 0.20           # 20% — máximo que o dado pode sortear
_BATALHA_ROUBO_TETO = 500           # teto máximo de XP roubado por batalha — sem isso, quem
                                      # já é rank alto rouba uma quantidade cada vez maior de
                                      # quem também é rank alto (ou parecido), ficando desigual
                                      # contra o rank baixo. Ajuste pra combinar com seu servidor.

# ══════════════════════════════════════════════════════════════════════
# ⚡ GOLPES ESPECIAIS — chance rara de aparecer no meio de um desafio
# (`.eu te desafio @alguém`). Quando surge, o golpe é sempre do lado de
# quem venceu a batalha: além de vencer, a criatura solta um ataque nomeado
# e turbina o saque de XP daquela vitória (mínimo e máximo de roubo mais
# altos que o normal). É sorte pura — não depende de raridade nem de Nível
# de Capacidade, pra qualquer criatura poder puxar um a qualquer momento.
# ══════════════════════════════════════════════════════════════════════
_CHANCE_GOLPE_ESPECIAL = 0.12   # 12% de chance de aparecer em cada desafio

# Enquanto o golpe especial está ativo, o roubo de XP usa essa faixa turbinada
# em vez de _BATALHA_ROUBO_MIN / _BATALHA_ROUBO_MAX — e ignora totalmente a
# chance de "não roubar nada" (_BATALHA_CHANCE_SEM_ROUBO).
_GOLPE_ESPECIAL_ROUBO_MIN = 0.15    # 15%
_GOLPE_ESPECIAL_ROUBO_MAX = 0.35    # 35%
_GOLPE_ESPECIAL_ROUBO_TETO = 800    # teto máximo de XP roubado com Golpe Especial — mais alto
                                      # que o teto normal (é sorte rara, merece ser melhor), mas
                                      # ainda travado pra não ficar desigual entre rank baixo e alto.

_GOLPES_ESPECIAIS = [
    {"nome": "Investida das Sombras",   "emoji": "🌑", "frase": "atravessa o adversário como um sopro de trevas"},
    {"nome": "Lâmina de Névoa",         "emoji": "🌫️", "frase": "corta a distância antes que o outro perceba"},
    {"nome": "Chama Ancestral",         "emoji": "🔥", "frase": "solta um rugido em fogo puro"},
    {"nome": "Golpe do Eclipse",        "emoji": "🌘", "frase": "cobre tudo em escuridão por um instante e ataca"},
    {"nome": "Fúria Estelar",           "emoji": "🌟", "frase": "brilha antes de acertar em cheio"},
    {"nome": "Investida do Abismo",     "emoji": "🌀", "frase": "puxa o adversário pro fundo e nocauteia"},
    {"nome": "Garra Relâmpago",         "emoji": "⚡", "frase": "ataca rápido demais pra ser visto"},
    {"nome": "Sopro Glacial",           "emoji": "❄️", "frase": "congela o momento e desfere o golpe final"},
]


def _sortear_golpe_especial() -> dict | None:
    """Sorteia se um Golpe Especial aparece nessa batalha (_CHANCE_GOLPE_ESPECIAL)
    e, se sim, qual dos golpes da lista foi. Retorna None quando não aparece."""
    if random.random() >= _CHANCE_GOLPE_ESPECIAL:
        return None
    return random.choice(_GOLPES_ESPECIAIS)


# ══════════════════════════════════════════════════════════════════════
# 📜 LOGS DO RPG — canal fixo onde TODO ganho orgânico do jogo (criatura
# nova, Besta, Mítico, XP saqueado/golpe especial, prêmio de baú, ovo
# chocando etc.) é anunciado com o motivo.
#
# ⚠️ De propósito, NUNCA passa por aqui nada que venha de comando
# administrativo do Reality/CRIADOR_ID — .darcriatura, .uparcriatura,
# .vantagem (a concessão em si), .darbosster, .bostercall, .darlevel,
# .ovo (a concessão em si), .reiniciarcriaturas, .reiniciarranking,
# .xpbackfill, .destravarbesta/corrigirbesta/checarbesta,
# .destravarpet/corrigirpet/checarpet, .rankingdebug,
# .xpdebug, .castigo — esses são ajustes manuais internos, não "ganhos" do
# jogo, e não devem aparecer no log. Batalhas onde uma Vantagem foi usada
# nos bastidores CONTINUAM sendo logadas normalmente (como uma vitória
# comum) — é assim que o resto do bot já trata isso, pra manter a
# encenação de que não foi arranjada.
# ══════════════════════════════════════════════════════════════════════
CANAL_LOGS_RPG_ID = 1536873513325957251  # canal de logs do RPG


async def _log_rpg(guild: discord.Guild, titulo: str, descricao: str, cor: int = 0x9b59b6) -> None:
    """Manda uma entrada no canal de logs do RPG (CANAL_LOGS_RPG_ID). Silencioso
    se o canal não existir ou o bot não tiver permissão — nunca quebra o fluxo
    principal do jogo por causa do log."""
    if guild is None:
        return
    canal = guild.get_channel(CANAL_LOGS_RPG_ID)
    if canal is None:
        return
    embed = discord.Embed(title=titulo, description=descricao, color=cor, timestamp=discord.utils.utcnow())
    embed.set_footer(text="📜 Renan — Logs do RPG")
    try:
        await canal.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass

# ── Hierarquia de força das raridades ──────────────────────────────────────
# Cada raridade tem uma força relativa (_ORDEM_RARIDADES, do mais forte pro
# mais fraco: 🐉 Mítico > 🌌 Secreto > 🦴 Fóssil > 🐺 Bestas > 🌀 Elemental > 🟡 Lendário > 🟣 Épico > 🔵 Raro > ⚪ Comum).
# Quanto maior a distância de raridade entre duas criaturas, mais a balança
# pende pro lado mais forte — mas o lado mais fraco NUNCA fica com chance zero.
# Um ⚪ Comum sempre pode dar a zebra contra um 🟣 Épico, só que é raro.
# Chave = quantos "degraus" de raridade separam as duas criaturas na
# hierarquia (0 = mesma raridade, 7 = a maior distância possível).
_CHANCE_VITORIA_POR_DEGRAU = {
    0: 0.50,   # mesma raridade — força bruta pura, sorteio justo
    1: 0.63,   # 1 degrau de diferença (ex: 🔵 Raro vs ⚪ Comum)
    2: 0.74,   # 2 degraus de diferença (ex: 🟣 Épico vs ⚪ Comum)
    3: 0.83,   # 3 degraus de diferença (ex: 🟡 Lendário vs ⚪ Comum)
    4: 0.90,   # 4 degraus de diferença (ex: 🐺 Bestas vs ⚪ Comum)
    5: 0.93,   # 5 degraus de diferença (ex: 🦴 Fóssil vs ⚪ Comum)
    6: 0.96,   # 6 degraus de diferença (ex: 🌌 Secreto vs ⚪ Comum)
    7: 0.98,   # 7 degraus de diferença (ex: 🐉 Mítico vs 🔵 Raro)
    8: 0.99,   # 8 degraus — a maior distância possível, agora que 🌀 Elemental entrou
               # na hierarquia (🐉 Mítico vs ⚪ Comum)
}

# Excepção específica: 🟡 Lendário contra 🐉 Mítico OU 🌌 Secreto é MUITO mais
# desigual do que a tabela por degraus normal sugeriria. Aqui o lado mais forte
# (Mítico ou Secreto) fica com uma chance bem acima do teto normal de 95%, e o
# Lendário sobra só com uma fresta mínima pra dar a zebra. Isso NÃO afeta outros
# pares que também têm a mesma distância de degraus (ex: 🌌 Secreto vs 🟣 Épico) —
# só esses dois confrontos específicos contra o Lendário.
_CHANCE_VITORIA_LENDARIO_MITICO  = 0.99   # chance do Mítico  (o lado mais forte do par)
_CHANCE_VITORIA_LENDARIO_SECRETO = 0.97   # chance do Secreto (o lado mais forte do par)
_CHANCE_VITORIA_PAR_ESPECIAL = {
    frozenset({"lendario", "mitico"}):  _CHANCE_VITORIA_LENDARIO_MITICO,
    frozenset({"lendario", "secreto"}): _CHANCE_VITORIA_LENDARIO_SECRETO,
}


def _chance_vitoria_por_raridade(raridade_a: str, raridade_b: str) -> float:
    """Devolve a chance de uma criatura de raridade `raridade_a` vencer uma
    de raridade `raridade_b`, seguindo a hierarquia de força das raridades.
    Quanto mais forte a raridade (e maior a distância entre elas), maior a
    chance de vitória — mas o lado mais fraco sempre mantém uma chance real
    de virar o jogo, por menor que seja. Pares listados em
    _CHANCE_VITORIA_PAR_ESPECIAL pulam a conta por degrau e usam o valor fixo
    definido lá (esse valor ainda passa pelo ajuste de Nível de Capacidade
    em _chance_vitoria, então o resultado final pode variar um pouco)."""
    indice_a = _ORDEM_RARIDADES.index(raridade_a)   # 0 = 🐉 Mítico (mais forte) ... 4 = ⚪ Comum (mais fraco)
    indice_b = _ORDEM_RARIDADES.index(raridade_b)

    par_especial = _CHANCE_VITORIA_PAR_ESPECIAL.get(frozenset({raridade_a, raridade_b}))
    if par_especial is not None:
        chance_do_mais_forte = par_especial
    else:
        degrau = abs(indice_a - indice_b)
        chance_do_mais_forte = _CHANCE_VITORIA_POR_DEGRAU.get(degrau, 0.95)

    if indice_a < indice_b:      # A é a raridade mais forte
        return chance_do_mais_forte
    elif indice_a > indice_b:    # B é a raridade mais forte
        return 1.0 - chance_do_mais_forte
    return 0.5                   # mesma raridade


# ══════════════════════════════════════════════════════════════════════
# CAPACIDADE DE NÍVEL — cada criatura, além da raridade, tem um Nível de
# Capacidade individual (de 1 a 10) POR PESSOA. Toda criatura desbloqueada
# começa no Nível 1; quanto mais vezes ela é invocada em batalha (ganhando
# ou perdendo, não importa), mais ela "sobe de nível", até o teto de 10.
# Isso significa que duas pessoas com a MESMA criatura (mesma raridade)
# podem ter forças diferentes: quem mais batalhou com ela leva vantagem.
# ══════════════════════════════════════════════════════════════════════

_NIVEL_CRIATURA_MAX = 10

# Quantos USOS ACUMULADOS são necessários pra estar em cada nível. Índice 0
# (0 usos) já garante o Nível 1; índice 1 é o mínimo de usos pro Nível 2;
# e assim por diante até o índice 9, mínimo pro Nível 10 (o teto). Os
# degraus crescem aos poucos — fica mais rápido subir no começo e mais
# custoso lá no topo, pra o Nível 10 realmente significar "muito usada".
_NIVEL_CRIATURA_USOS_ACUMULADOS = [0, 3, 7, 12, 18, 25, 33, 42, 52, 63]

# Teto (e tabela de usos) especial para criaturas específicas — não é
# documentado/anunciado em nenhum lugar do bot de propósito. Continua a
# mesma progressão de dificuldade da tabela normal, só que até o Nível 20
# em vez de 10.
_NIVEL_CRIATURA_MAX_ESPECIAL = {"vorakthul": 20}
_NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO = _NIVEL_CRIATURA_USOS_ACUMULADOS + [
    75, 88, 102, 117, 133, 150, 168, 187, 207, 228,
]

# Quanto cada DEGRAU de diferença de nível pesa na chance de vitória (ex:
# nível 1 vs nível 3 = 2 degraus de diferença). É um ajuste mais discreto
# que o da raridade — o nível refina a disputa, não a domina.
_NIVEL_CRIATURA_BONUS_POR_DEGRAU = 0.03

# Trava de segurança: mesmo com raridade E nível somados a favor de um
# lado, ninguém fica com 0% (ou 100%) de chance — sempre sobra uma brecha.
_CHANCE_VITORIA_MINIMA = 0.05
_CHANCE_VITORIA_MAXIMA = 0.95

# Trava separada e bem mais folgada, só pra confrontos listados em
# _CHANCE_VITORIA_PAR_ESPECIAL (Lendário x Mítico / Lendário x Secreto). Sem
# isso, os 99%/97% definidos ali em cima seriam cortados de volta pro teto
# normal de 95% — aqui a discrepância desses dois confrontos pode ir bem
# além disso, mesmo depois do ajuste de Nível de Capacidade.
_CHANCE_VITORIA_MINIMA_PAR_ESPECIAL = 0.01
_CHANCE_VITORIA_MAXIMA_PAR_ESPECIAL = 0.99


def _nivel_criatura_max(criatura_id: str = None) -> int:
    """Teto de Nível de Capacidade pra essa criatura — normalmente
    _NIVEL_CRIATURA_MAX (10), exceto pras que estão em
    _NIVEL_CRIATURA_MAX_ESPECIAL."""
    return _NIVEL_CRIATURA_MAX_ESPECIAL.get(criatura_id, _NIVEL_CRIATURA_MAX)


def _calcular_nivel_criatura(usos: int, criatura_id: str = None) -> int:
    """Converte quantos usos uma criatura já teve no Nível de Capacidade
    correspondente, de acordo com _NIVEL_CRIATURA_USOS_ACUMULADOS (ou a
    tabela estendida, pras criaturas em _NIVEL_CRIATURA_MAX_ESPECIAL)."""
    tabela = _NIVEL_CRIATURA_USOS_ACUMULADOS
    if criatura_id in _NIVEL_CRIATURA_MAX_ESPECIAL:
        tabela = _NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO
    nivel = 1
    for indice, limite in enumerate(tabela):
        if usos >= limite:
            nivel = indice + 1
    return min(nivel, _nivel_criatura_max(criatura_id))


def _usos_criatura(user_id: int, criatura_id: str) -> int:
    """Quantas vezes essa pessoa já usou essa criatura em batalha."""
    dados = xp_stats[user_id]
    dados.setdefault("usos_criaturas", {})
    return dados["usos_criaturas"].get(criatura_id, 0)


def _nivel_criatura(user_id: int, criatura_id: str) -> int:
    """Nível de Capacidade atual dessa criatura, PRA ESSA pessoa."""
    return _calcular_nivel_criatura(_usos_criatura(user_id, criatura_id), criatura_id)


def _registrar_uso_criatura(user_id: int, criatura_id: str) -> tuple:
    """Soma mais 1 uso a essa criatura (pra essa pessoa) e devolve
    (nivel_antigo, nivel_novo) — útil pra saber se ela acabou de subir
    de Nível de Capacidade com esse uso."""
    dados = xp_stats[user_id]
    dados.setdefault("usos_criaturas", {})
    usos_antes = dados["usos_criaturas"].get(criatura_id, 0)
    nivel_antigo = _calcular_nivel_criatura(usos_antes, criatura_id)
    usos_depois = usos_antes + 1
    dados["usos_criaturas"][criatura_id] = usos_depois
    nivel_novo = _calcular_nivel_criatura(usos_depois, criatura_id)
    return nivel_antigo, nivel_novo


def _chance_vitoria(criatura_a: dict, nivel_a: int, criatura_b: dict, nivel_b: int) -> float:
    """Chance da criatura A vencer a criatura B, combinando a hierarquia de
    raridade (_chance_vitoria_por_raridade) com o ajuste fino do Nível de
    Capacidade de cada uma: pra cada degrau de nível a mais, um pequeno
    empurrão a mais na balança. Travado entre 5% e 95% no caso normal — mas
    os pares especiais (Lendário x Mítico / Lendário x Secreto) usam a trava
    mais folgada (1%/99%), já que a ideia ali é justamente uma discrepância
    bem maior que a de qualquer outro confronto."""
    chance_base = _chance_vitoria_por_raridade(criatura_a["raridade"], criatura_b["raridade"])
    ajuste_nivel = (nivel_a - nivel_b) * _NIVEL_CRIATURA_BONUS_POR_DEGRAU

    par = frozenset({criatura_a["raridade"], criatura_b["raridade"]})
    if par in _CHANCE_VITORIA_PAR_ESPECIAL:
        minimo, maximo = _CHANCE_VITORIA_MINIMA_PAR_ESPECIAL, _CHANCE_VITORIA_MAXIMA_PAR_ESPECIAL
    else:
        minimo, maximo = _CHANCE_VITORIA_MINIMA, _CHANCE_VITORIA_MAXIMA

    return max(minimo, min(maximo, chance_base + ajuste_nivel))


# ══════════════════════════════════════════════════════════════════════
# 🐺 BESTAS — raridade desbloqueada por CONQUISTA, não por sorteio. Mais
# fortes que as Lendárias, mas ainda um degrau abaixo das Secretas. A única
# forma de conseguir uma é levando uma criatura ⚪ Comum, 🔵 Raro, 🟣 Épico
# ou 🟡 Lendário até o Nível de Capacidade máximo (_NIVEL_CRIATURA_MAX) —
# ao bater esse nível, a pessoa recebe automaticamente, de graça, 1 Besta
# sorteada dentre as do "tier" correspondente (as que ela ainda não tiver).
# Nunca aparecem no sorteio normal de recompensa de batalha nem no 🪙 Baú —
# só saem por esse caminho.
# ══════════════════════════════════════════════════════════════════════

# tier de origem (raridade da criatura que bateu o Nível máximo) -> lista de
# ids de Bestas que podem ser concedidas quando isso acontece.
_BESTAS_POR_TIER = {
    "comum":    ["kragor_senhor_presas", "espinho_maldito"],
    "raro":     ["drogan_carniceiro", "matriarca_abismo"],
    "epico":    ["venomor"],
    "lendario": ["ultimo_shogun_trevas"],
}


def _checar_desbloqueio_besta(user_id: int, criatura: dict, nivel_antigo: int, nivel_novo: int):
    """Se `criatura` acabou de bater o Nível de Capacidade máximo dela AGORA
    (ou seja, subiu de nível nessa mesma batalha e o nível novo já é o teto)
    e a raridade dela tem um tier de Bestas associado, sorteia 1 Besta ainda
    não possuída daquele tier e concede pra `user_id`. Devolve a Besta
    concedida (dict) ou None se nada foi desbloqueado."""
    tier = _BESTAS_POR_TIER.get(criatura["raridade"])
    if not tier:
        return None
    if not (nivel_novo > nivel_antigo and nivel_novo >= _nivel_criatura_max(criatura["id"])):
        return None

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    faltando = [c for c in _BATALHA_CRIATURAS if c["id"] in tier and c["id"] not in dados["criaturas"]]
    if not faltando:
        return None

    besta_nova = random.choice(faltando)
    dados["criaturas"].append(besta_nova["id"])
    return besta_nova


# Canal onde todo desbloqueio de 🐺 Besta é anunciado — mesmo canal do chat
# geral (_XP_CANAL_1 = 1284257046740602901).
_BESTA_ANUNCIO_CANAL_ID = 1501260061530390563  # canal de anúncios do RPG


async def _anunciar_besta_desbloqueada(
    guild: discord.Guild, membro: discord.Member, criatura_origem: dict, besta: dict
) -> None:
    """Manda, no canal fixo _BESTA_ANUNCIO_CANAL_ID, o anúncio de que `membro`
    destravou a 🐺 Besta `besta` ao levar `criatura_origem` até o Nível de
    Capacidade máximo. Não apaga sozinho — fica registrado no canal."""
    canal = guild.get_channel(_BESTA_ANUNCIO_CANAL_ID)
    if canal is None:
        return

    info_raridade_besta = _RARIDADES["bestas"]
    teto = _nivel_criatura_max(criatura_origem["id"])

    embed = discord.Embed(
        title="🐺 Besta Destravada!",
        description=(
            f"⚡ **{membro.display_name}** levou **{criatura_origem['nome']}** até o "
            f"**Nível de Capacidade máximo** (`{teto}/{teto}`) e, como conquista, destravou "
            f"{info_raridade_besta['emoji']} **{besta['nome']}** (*{info_raridade_besta['label']}*)!!\n\n"
            "👽 **Renan:** ...uma conquista de verdade, ganha com treino. Eu aprovo. "
            f"{membro.mention} treinou, suou e conquistou isso."
        ),
        color=info_raridade_besta["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=membro.display_name, icon_url=membro.display_avatar.url)
    embed.set_image(url=besta["gif"])
    embed.set_footer(text="👽 Renan — Arena de Batalhas")

    try:
        await canal.send(content=membro.mention, embed=embed)
    except discord.HTTPException:
        pass


# Canal onde todo desbloqueio de 🦴 Fóssil é anunciado — mesmo canal do chat
# geral (_XP_CANAL_1 = 1284257046740602901), igual ao anúncio de Besta.
_FOSSIL_ANUNCIO_CANAL_ID = 1501260061530390563  # canal de anúncios do RPG


async def _anunciar_fossil_desbloqueado(
    guild: discord.Guild, membro: discord.Member, fossil: dict
) -> None:
    """Manda, no canal fixo _FOSSIL_ANUNCIO_CANAL_ID, o anúncio de que `membro`
    desenterrou o 🦴 Fóssil `fossil` — sempre mencionando a pessoa E o nome
    da criatura. Só é chamado quando os dois lados da batalha estavam numa
    call de voz e a rolagem de _FOSSIL_CHANCE_DESBLOQUEIO deu certo."""
    canal = guild.get_channel(_FOSSIL_ANUNCIO_CANAL_ID)
    if canal is None:
        return

    info_raridade_fossil = _RARIDADES["fosseis"]

    embed = discord.Embed(
        title="🦴 Fóssil Desenterrado!",
        description=(
            f"🎧 Os dois lados da batalha estavam numa call de voz, e o dado só tinha "
            f"`{_FOSSIL_CHANCE_DESBLOQUEIO * 100:.0f}%` de chance — mas **{membro.display_name}** "
            f"desenterrou {info_raridade_fossil['emoji']} **{fossil['nome']}** "
            f"(*{info_raridade_fossil['label']}*)!!\n\n"
            "👽 **Renan:** ...algo raro veio à tona. Eu sinto o peso dos séculos nisso. "
            f"Sorte absurda, {membro.mention} — achado de call, achado de sorte."
        ),
        color=info_raridade_fossil["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=membro.display_name, icon_url=membro.display_avatar.url)
    embed.set_image(url=fossil["gif"])
    embed.set_footer(text="👽 Renan — Arena de Batalhas")

    try:
        await canal.send(content=membro.mention, embed=embed)
    except discord.HTTPException:
        pass


def _forcar_verificacao_besta(user_id: int, criatura: dict):
    """Versão 'preguiçosa' de _checar_desbloqueio_besta: em vez de exigir que
    o Nível de Capacidade tenha acabado de subir NESSA hora, só olha o
    estado atual — se `criatura` já está no nível máximo dela pra essa
    pessoa. Usada pelo comando `.destravarbesta`, que existe pra corrigir
    manualmente os casos em que o desbloqueio automático (em batalha) falhou
    ou não foi anunciado. Sortear e conceder a Besta segue seguro contra
    duplicação: só concede se ainda faltar alguma Besta daquele tier na
    coleção da pessoa (mesma checagem de sempre)."""
    tier = _BESTAS_POR_TIER.get(criatura["raridade"])
    if not tier:
        return None
    if _nivel_criatura(user_id, criatura["id"]) < _nivel_criatura_max(criatura["id"]):
        return None

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    faltando = [c for c in _BATALHA_CRIATURAS if c["id"] in tier and c["id"] not in dados["criaturas"]]
    if not faltando:
        return None

    besta_nova = random.choice(faltando)
    dados["criaturas"].append(besta_nova["id"])
    return besta_nova


# ══════════════════════════════════════════════════════════════════════
# 🌀 ELEMENTAIS — raridade desbloqueada por CONQUISTA, não por sorteio. Mais
# fortes que as Lendárias, mas ainda um degrau abaixo das Bestas. A única
# forma de conseguir um é levando uma criatura 🟣 Épica até o Nível de
# Capacidade `_ELEMENTAL_NIVEL_DESBLOQUEIO` (6, não precisa ser o teto) —
# ao bater esse nível, a pessoa recebe automaticamente, de graça, 1
# Elemental ALEATÓRIO dentre os que ainda não tiver (diferente das Bestas,
# não existe "tier" — todos os 12 Elementais entram no mesmo sorteio).
# Nunca aparecem no sorteio normal de recompensa de batalha nem no 🪙 Baú/
# `.ovo` — só saem por esse caminho.
#
# Além do desbloqueio, todo Elemental USADO numa batalha de desafio
# ("eu te desafio @alguém") — convocado, ganhando ou perdendo, não importa
# — concede na hora, pra quem o convocou, um Booster de xp em dobro por
# `_ELEMENTAL_BOOSTER_MINUTOS` minutos (empilha em cima de qualquer
# booster que a pessoa já tiver ativo — ver _executar_batalha).
# ══════════════════════════════════════════════════════════════════════

# Só criaturas 🟣 Épicas concedem Elemental, sempre ao bater ESSE Nível de
# Capacidade específico (não precisa ser o teto — igual os Pets, diferente
# das Bestas).
_ELEMENTAL_NIVEL_DESBLOQUEIO = 6

# Quanto tempo de Booster de xp em dobro (mesmo multiplicador de sempre,
# _BAU_BOOSTER_MULTIPLICADOR) cada USO de um Elemental em batalha concede.
_ELEMENTAL_BOOSTER_MINUTOS = 2


def _checar_desbloqueio_elemental(user_id: int, criatura: dict, nivel_antigo: int, nivel_novo: int):
    """Se `criatura` é 🟣 Épica e acabou de bater o Nível de Capacidade
    `_ELEMENTAL_NIVEL_DESBLOQUEIO` (6) AGORA — subiu de nível nessa mesma
    batalha e o nível novo já bate ou passa esse marco, o antigo ainda não
    batia — sorteia 1 Elemental ainda não possuído (dentre TODOS os 12,
    sem distinção de tier) e concede pra `user_id`. Devolve o Elemental
    concedido (dict) ou None se nada foi desbloqueado."""
    if criatura["raridade"] != "epico":
        return None
    if not (
        nivel_novo > nivel_antigo
        and nivel_novo >= _ELEMENTAL_NIVEL_DESBLOQUEIO
        and nivel_antigo < _ELEMENTAL_NIVEL_DESBLOQUEIO
    ):
        return None

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    faltando = [c for c in _BATALHA_CRIATURAS if c["raridade"] == "elemental" and c["id"] not in dados["criaturas"]]
    if not faltando:
        return None

    elemental_novo = random.choice(faltando)
    dados["criaturas"].append(elemental_novo["id"])
    return elemental_novo


def _forcar_verificacao_elemental(user_id: int, criatura: dict):
    """Versão 'preguiçosa' de _checar_desbloqueio_elemental: em vez de
    exigir que o Nível de Capacidade tenha acabado de subir NESSA hora, só
    olha o estado atual — se `criatura` já está no Nível 6 ou mais pra essa
    pessoa. Usada pelo comando `.destravarelemental`, que existe pra
    corrigir manualmente os casos em que o desbloqueio automático (em
    batalha) falhou ou não foi anunciado."""
    if criatura["raridade"] != "epico":
        return None
    if _nivel_criatura(user_id, criatura["id"]) < _ELEMENTAL_NIVEL_DESBLOQUEIO:
        return None

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    faltando = [c for c in _BATALHA_CRIATURAS if c["raridade"] == "elemental" and c["id"] not in dados["criaturas"]]
    if not faltando:
        return None

    elemental_novo = random.choice(faltando)
    dados["criaturas"].append(elemental_novo["id"])
    return elemental_novo


async def _anunciar_elemental_desbloqueado(
    guild: discord.Guild, membro: discord.Member, criatura_origem: dict, elemental: dict
) -> None:
    """Manda, no canal fixo _BESTA_ANUNCIO_CANAL_ID (mesmo do chat geral),
    o anúncio de que `membro` destravou o Elemental `elemental` ao levar
    `criatura_origem` até o Nível de Capacidade `_ELEMENTAL_NIVEL_DESBLOQUEIO`."""
    canal = guild.get_channel(_BESTA_ANUNCIO_CANAL_ID)
    if canal is None:
        return

    info_raridade_elemental = _RARIDADES["elemental"]

    embed = discord.Embed(
        title="🌀 Elemental Destravado!",
        description=(
            f"⚡ **{membro.display_name}** levou **{criatura_origem['nome']}** até o "
            f"**Nível de Capacidade `{_ELEMENTAL_NIVEL_DESBLOQUEIO}`** e, como conquista, destravou "
            f"{info_raridade_elemental['emoji']} **{elemental['nome']}** "
            f"(*{info_raridade_elemental['label']}*)!!\n\n"
            f"✨ A partir de agora, toda vez que **{elemental['nome']}** for convocado numa batalha, "
            f"{membro.display_name} ganha um Booster de xp em dobro por `{_ELEMENTAL_BOOSTER_MINUTOS} min`!\n\n"
            "👽 **Renan:** ...uma força elemental, desperta. Eu respeito isso. "
            f"{membro.mention} destravou um Elemental — olha esse poder."
        ),
        color=info_raridade_elemental["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=membro.display_name, icon_url=membro.display_avatar.url)
    embed.set_image(url=elemental["gif"])
    embed.set_footer(text="👽 Renan — Arena de Batalhas")

    try:
        await canal.send(content=membro.mention, embed=embed)
    except discord.HTTPException:
        pass


# ══════════════════════════════════════════════════════════════════════
# 🐾 PETS — desbloqueados quando uma criatura 🔵 Rara sua bate o Nível de
# Capacidade 4 pela PRIMEIRA vez: na hora, sorteia (de graça) 1 Pet dentre
# os que você ainda não tem — igualzinho ao desbloqueio de 🐺 Besta (ver
# _checar_desbloqueio_besta acima), só que fixo no Nível 4 em vez do teto,
# e exclusivo das criaturas Raras.
#
# Pets NÃO entram em batalha PvP (não são "criaturas") — são só SUPORTE
# pro Boss: quando EQUIPADO (`.equiparpet <nome>`), o Pet soma um bônus
# fixo na chance de vencer QUALQUER Boss (entre 2% e 5%, crescendo com o
# Nível do próprio Pet) e tem uma chance de upar +1 o Nível de Capacidade
# de uma das suas criaturas toda vez que participa de uma VITÓRIA contra
# um Boss. Pets têm Nível de 1 a 5 — e SÓ sobem enfrentando Boss (vencendo
# ou perdendo, não importa, igual criatura) — e destravam uma habilidade
# especial própria, diferente pra cada Pet, ao chegar no Nível 3.
# ══════════════════════════════════════════════════════════════════════

_PET_NIVEL_MAX = 5
_PET_NIVEL_HABILIDADE = 3   # nível em que a habilidade especial de cada Pet é destravada

# Quantos confrontos de Boss (vencendo ou perdendo — só precisa PARTICIPAR
# com o Pet equipado) são necessários pra cada Nível. Índice 0 (0 usos) já
# garante o Nível 1; índice 4 é o mínimo pro Nível 5 (o teto).
_PET_NIVEL_USOS_ACUMULADOS = [0, 2, 5, 9, 14]

# Bônus na chance de vencer um Boss (soma direto na chance final, igual o
# bônus de raridade de criatura convocada) de acordo com o Nível do Pet
# EQUIPADO — sobe linear de 2% (Nível 1) até 5% (Nível 5).
_PET_BONUS_BOSS_NIVEL1 = 0.02
_PET_BONUS_BOSS_NIVEL5 = 0.05

# Chance-base do Pet equipado upar em +1 o Nível de Capacidade de uma
# criatura aleatória (dentre as que ainda não estão no teto) toda vez que
# ele participa de uma VITÓRIA contra um Boss.
_PET_CHANCE_UPAR_CRIATURA = 0.20

# Só criaturas 🔵 Raras concedem Pet, sempre ao bater ESSE Nível de
# Capacidade específico (não precisa ser o teto — diferente das Bestas).
_PET_NIVEL_DESBLOQUEIO = 4

_PETS = [
    {
        "id": "monstrinho",
        "nome": "Monstrinho",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410248198258888/1785186432942.gif?ex=6a691c6f&is=6a67caef&hm=4432eae4146ab6da26807f04c75dbde63df9f7dc4cad6ab13466b5ee86e2d57d&",
        "habilidade_nome": "🍖 Voracidade",
        "habilidade_descricao": "Soma +20 pontos percentuais na chance dele upar uma criatura sua depois de vencer um Boss.",
        "habilidade_tipo": "chance_upar_extra",
        "habilidade_valor": 0.20,
    },
    {
        "id": "vampy",
        "nome": "Vampy",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410247774900438/1785186421135.gif?ex=6a691c6f&is=6a67caef&hm=efa2f12767946aab1c7de01f05c655ab71f59fbceeaa7af6200d33ef7e93323e&",
        "habilidade_nome": "🩸 Sede Ancestral",
        "habilidade_descricao": "Suga um extra de `40` a `120` XP direto pra você sempre que vencem um Boss juntos.",
        "habilidade_tipo": "xp_flat_vitoria",
        "habilidade_valor": (40, 120),
    },
    {
        "id": "kitsura",
        "nome": "Kitsura",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410248500379648/1785186503259.gif?ex=6a691c6f&is=6a67caef&hm=c1fbc8ec4a818715875587c06071141004463e71a725b8af9586e0ae335e757d&",
        "habilidade_nome": "🦊 Ilusão da Raposa",
        "habilidade_descricao": "A chance dela upar uma criatura sua depois de vencer um Boss vira GARANTIDA (100%).",
        "habilidade_tipo": "upar_garantido",
        "habilidade_valor": None,
    },
    {
        "id": "drax",
        "nome": "Drax",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410248802504847/1785186661353.gif?ex=6a691c6f&is=6a67caef&hm=28f50e34bfbf2fee22720bd4d24cdc7d319ff63d4fc8add71dd737130353f404&",
        "habilidade_nome": "🔥 Fúria Draconiana",
        "habilidade_descricao": "Soma mais `+2%` fixos na chance de vencer QUALQUER Boss, além do bônus normal do Nível dele.",
        "habilidade_tipo": "bonus_chance_extra",
        "habilidade_valor": 0.02,
    },
    {
        "id": "lilo",
        "nome": "Lilo",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410249125203999/1785186871194.gif?ex=6a691c6f&is=6a67caef&hm=c719c8464520ddef5ca5593bc2bfc286b872770f964ae6c3c66dd4d87b0e639e&",
        "habilidade_nome": "🌙 Consolo Selvagem",
        "habilidade_descricao": "Mesmo numa DERROTA contra o Boss, garante um consolo de `20` a `60` XP.",
        "habilidade_tipo": "xp_flat_derrota",
        "habilidade_valor": (20, 60),
    },
    {
        "id": "renan",
        "nome": "Renan",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410249431646359/1785186907093.gif?ex=6a691c6f&is=6a67caef&hm=96d4a27952131d1d8d0b41a504d92bfbbeb50d551334f6b73d3c31ed1916bf49&",
        "habilidade_nome": "👽 Presença do Último",
        "habilidade_descricao": "Soma `+1%` na chance de vitória em GRUPO contra o Boss pra CADA outro participante da batalha.",
        "habilidade_tipo": "bonus_grupo_participante",
        "habilidade_valor": 0.01,
    },
    {
        "id": "loki",
        "nome": "Loki",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410249813065955/1785186977070.gif?ex=6a691c6f&is=6a67caef&hm=327467c57a994e455420f5a59d77319be3f381ada027e5f324ba724dcab5c0fe&",
        "habilidade_nome": "🃏 Trapaça do Caos",
        "habilidade_descricao": "Soma mais `+3%` fixos na chance de vencer QUALQUER Boss, além do bônus normal do Nível dele.",
        "habilidade_tipo": "bonus_chance_extra",
        "habilidade_valor": 0.03,
    },
    {
        "id": "layla",
        "nome": "Layla",
        "gif": "https://cdn.discordapp.com/attachments/926913851172204577/1531410250266181752/1785187039526.gif?ex=6a691c6f&is=6a67caef&hm=9858b27fa61518fb3d4e61c3b46350151c8bdee861d4839fffd120b7fc97b998&",
        "habilidade_nome": "🌸 Bênção Silenciosa",
        "habilidade_descricao": "Soma +10 pontos percentuais na chance dela upar uma criatura sua depois de vencer um Boss.",
        "habilidade_tipo": "chance_upar_extra",
        "habilidade_valor": 0.10,
    },
]


def _pet_nivel_max() -> int:
    return _PET_NIVEL_MAX


def _calcular_nivel_pet(usos: int) -> int:
    """Converte quantos confrontos de Boss um Pet já participou (equipado)
    no Nível correspondente, de acordo com _PET_NIVEL_USOS_ACUMULADOS."""
    nivel = 1
    for indice, limite in enumerate(_PET_NIVEL_USOS_ACUMULADOS):
        if usos >= limite:
            nivel = indice + 1
    return min(nivel, _PET_NIVEL_MAX)


def _usos_pet(user_id: int, pet_id: str) -> int:
    """Quantos confrontos de Boss essa pessoa já enfrentou com esse Pet equipado."""
    dados = xp_stats[user_id]
    dados.setdefault("usos_pets", {})
    return dados["usos_pets"].get(pet_id, 0)


def _nivel_pet(user_id: int, pet_id: str) -> int:
    """Nível atual desse Pet, PRA ESSA pessoa."""
    return _calcular_nivel_pet(_usos_pet(user_id, pet_id))


def _registrar_uso_pet(user_id: int, pet_id: str) -> tuple:
    """Soma +1 confronto de Boss a esse Pet (pra essa pessoa) e devolve
    (nivel_antigo, nivel_novo) — útil pra saber se ele acabou de subir de
    Nível com esse confronto."""
    dados = xp_stats[user_id]
    dados.setdefault("usos_pets", {})
    usos_antes = dados["usos_pets"].get(pet_id, 0)
    nivel_antigo = _calcular_nivel_pet(usos_antes)
    usos_depois = usos_antes + 1
    dados["usos_pets"][pet_id] = usos_depois
    nivel_novo = _calcular_nivel_pet(usos_depois)
    return nivel_antigo, nivel_novo


def _encontrar_pet_por_nome(busca: str) -> dict:
    """Acha um Pet em _PETS a partir de um nome digitado (com ou sem
    acento/maiúsculas) — igual _encontrar_criatura_por_nome, só que pra Pets."""
    alvo = _normalizar_texto(busca)
    for p in _PETS:
        if _normalizar_texto(p["nome"]) == alvo:
            return p
    for p in _PETS:
        if _normalizar_texto(p["nome"]).startswith(alvo):
            return p
    candidatos = [p for p in _PETS if alvo in _normalizar_texto(p["nome"])]
    return candidatos[0] if len(candidatos) == 1 else None


def _pets_desbloqueados(user_id: int) -> list:
    """Lista de ids dos Pets já desbloqueados por essa pessoa."""
    dados = xp_stats[user_id]
    dados.setdefault("pets", [])
    return dados["pets"]


def _obter_pet_equipado(user_id: int) -> dict:
    """Devolve o dict do Pet atualmente EQUIPADO por essa pessoa, ou None
    se ela não tiver nenhum equipado (ou o equipado não existir mais)."""
    dados = xp_stats[user_id]
    pet_id = dados.get("pet_equipado")
    if not pet_id or pet_id not in _pets_desbloqueados(user_id):
        return None
    return next((p for p in _PETS if p["id"] == pet_id), None)


def _checar_desbloqueio_pet(user_id: int, criatura: dict, nivel_antigo: int, nivel_novo: int):
    """Se `criatura` é 🔵 Rara e acabou de bater o Nível de Capacidade
    `_PET_NIVEL_DESBLOQUEIO` (4) AGORA — subiu de nível nessa mesma
    batalha/ação e o nível novo já bate ou passa esse marco, o antigo
    ainda não batia — sorteia 1 Pet ainda não possuído e concede pra
    `user_id`. Devolve o Pet concedido (dict) ou None se nada foi
    desbloqueado (raridade errada, marco errado ou já tem todos os Pets)."""
    if criatura["raridade"] != "raro":
        return None
    if not (nivel_novo > nivel_antigo and nivel_novo >= _PET_NIVEL_DESBLOQUEIO and nivel_antigo < _PET_NIVEL_DESBLOQUEIO):
        return None

    dados = xp_stats[user_id]
    dados.setdefault("pets", [])
    faltando = [p for p in _PETS if p["id"] not in dados["pets"]]
    if not faltando:
        return None

    pet_novo = random.choice(faltando)
    dados["pets"].append(pet_novo["id"])
    return pet_novo


async def _anunciar_pet_desbloqueado(
    guild: discord.Guild, membro: discord.Member, criatura_origem: dict, pet: dict
) -> None:
    """Manda, no canal fixo _BESTA_ANUNCIO_CANAL_ID (mesmo do chat geral),
    o anúncio de que `membro` destravou o Pet `pet` ao levar `criatura_origem`
    até o Nível de Capacidade `_PET_NIVEL_DESBLOQUEIO`."""
    canal = guild.get_channel(_BESTA_ANUNCIO_CANAL_ID)
    if canal is None:
        return

    embed = discord.Embed(
        title="🐾 Pet Destravado!",
        description=(
            f"✨ **{membro.display_name}** levou **{criatura_origem['nome']}** até o "
            f"**Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}`** e, de recompensa, destravou "
            f"o Pet **{pet['nome']}**!!\n\n"
            f"Use `.equiparpet {pet['nome']}` pra equipar — Pets dão bônus na chance de vencer "
            "Boss e ajudam a upar suas criaturas!\n\n"
            f"👽 **Renan:** ...um novo companheiro. Eu aceito a companhia dele. {membro.mention} "
            "ganhou um Pet novo."
        ),
        color=0x9b59b6,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=membro.display_name, icon_url=membro.display_avatar.url)
    embed.set_image(url=pet["gif"])
    embed.set_footer(text="👽 Renan — Arena de Batalhas")

    try:
        await canal.send(content=membro.mention, embed=embed)
    except discord.HTTPException:
        pass


def _forcar_verificacao_pet(user_id: int, criatura: dict):
    """Versão 'preguiçosa' de _checar_desbloqueio_pet: em vez de exigir que
    o Nível de Capacidade tenha acabado de subir NESSA hora, só olha o
    estado atual — se `criatura` (🔵 Rara) já está no Nível de Capacidade
    `_PET_NIVEL_DESBLOQUEIO` ou acima, pra essa pessoa. Usada pelo comando
    `.destravarpet`, que existe pra corrigir manualmente os casos em que o
    desbloqueio automático (em batalha) falhou ou não foi anunciado.
    Sortear e conceder o Pet segue seguro contra duplicação: só concede se
    ainda faltar algum Pet na coleção da pessoa (mesma checagem de sempre)."""
    if criatura["raridade"] != "raro":
        return None
    if _nivel_criatura(user_id, criatura["id"]) < _PET_NIVEL_DESBLOQUEIO:
        return None

    dados = xp_stats[user_id]
    dados.setdefault("pets", [])
    faltando = [p for p in _PETS if p["id"] not in dados["pets"]]
    if not faltando:
        return None

    pet_novo = random.choice(faltando)
    dados["pets"].append(pet_novo["id"])
    return pet_novo


def _pet_bonus_chance_boss(user_id: int) -> float:
    """Bônus total (0.0 se ninguém tiver Pet equipado) que o Pet EQUIPADO
    dessa pessoa soma na chance de vencer um Boss: o bônus base do Nível
    dele (2% a 5%, linear) + o bônus extra da habilidade especial, SE ela
    for do tipo "bonus_chance_extra" e o Pet já tiver batido o Nível
    _PET_NIVEL_HABILIDADE."""
    pet = _obter_pet_equipado(user_id)
    if pet is None:
        return 0.0
    nivel = _nivel_pet(user_id, pet["id"])
    faixa = _PET_BONUS_BOSS_NIVEL5 - _PET_BONUS_BOSS_NIVEL1
    bonus = _PET_BONUS_BOSS_NIVEL1 + faixa * ((nivel - 1) / (_PET_NIVEL_MAX - 1))
    if nivel >= _PET_NIVEL_HABILIDADE and pet["habilidade_tipo"] == "bonus_chance_extra":
        bonus += pet["habilidade_valor"]
    return bonus


def _pet_bonus_grupo_extra(participantes: list) -> float:
    """Bônus extra de GRUPO da habilidade especial 'bonus_grupo_participante'
    (Renan): soma, pra CADA participante que tiver esse Pet
    equipado E já no Nível de habilidade, `valor` de bônus por CADA OUTRO
    participante da batalha."""
    bonus_total = 0.0
    for membro in participantes:
        pet = _obter_pet_equipado(membro.id)
        if pet is None or pet["habilidade_tipo"] != "bonus_grupo_participante":
            continue
        nivel = _nivel_pet(membro.id, pet["id"])
        if nivel >= _PET_NIVEL_HABILIDADE:
            bonus_total += pet["habilidade_valor"] * max(0, len(participantes) - 1)
    return bonus_total


def _pet_upar_criatura_aleatoria(user_id: int):
    """Escolhe, entre as criaturas já desbloqueadas dessa pessoa que AINDA
    não estão no Nível de Capacidade máximo, uma aleatória, e empurra os
    usos dela pro limiar mínimo do próximo Nível (mesma lógica do
    `.uparcriatura`). Devolve (criatura, nivel_novo, besta_nova, pet_novo)
    — besta_nova/pet_novo vêm preenchidos se esse "up" de brinde acabou de
    destravar uma Besta ou um Pet novo (cascata) — ou None se não tinha
    nenhuma criatura elegível pra upar."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))
    candidatas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] in desbloqueadas and _nivel_criatura(user_id, c["id"]) < _nivel_criatura_max(c["id"])
    ]
    if not candidatas:
        return None

    criatura = random.choice(candidatas)
    criatura_id = criatura["id"]
    nivel_antigo = _nivel_criatura(user_id, criatura_id)

    tabela = (
        _NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO
        if criatura_id in _NIVEL_CRIATURA_MAX_ESPECIAL
        else _NIVEL_CRIATURA_USOS_ACUMULADOS
    )
    dados = xp_stats[user_id]
    dados.setdefault("usos_criaturas", {})
    dados["usos_criaturas"][criatura_id] = max(
        dados["usos_criaturas"].get(criatura_id, 0),
        tabela[nivel_antigo],   # limiar de usos mínimos pro PRÓXIMO nível
    )
    nivel_novo = _calcular_nivel_criatura(dados["usos_criaturas"][criatura_id], criatura_id)

    besta_nova = _checar_desbloqueio_besta(user_id, criatura, nivel_antigo, nivel_novo)
    pet_novo = _checar_desbloqueio_pet(user_id, criatura, nivel_antigo, nivel_novo)

    return criatura, nivel_novo, besta_nova, pet_novo


async def _pet_pos_boss(guild: discord.Guild, membro: discord.Member, venceu: bool):
    """Chamada depois de CADA confronto de Boss (solo ou grupo, vencendo
    ou perdendo) pra CADA participante: registra +1 uso no Pet EQUIPADO
    dessa pessoa (se tiver algum), checa se ele upou de Nível, e aplica os
    efeitos de suporte (chance de upar uma criatura na vitória, habilidade
    especial a partir do Nível 3...). Devolve um texto pronto (ou None) pra
    encaixar no resultado do Boss."""
    pet = _obter_pet_equipado(membro.id)
    if pet is None:
        return None

    nivel_antigo, nivel_novo = _registrar_uso_pet(membro.id, pet["id"])
    habilidade_ativa = nivel_novo >= _PET_NIVEL_HABILIDADE
    partes = []

    if nivel_novo > nivel_antigo:
        partes.append(f"🐾 **{pet['nome']}** ({membro.display_name}) subiu pro Nível `{nivel_novo}/{_PET_NIVEL_MAX}`!")
        if nivel_novo == _PET_NIVEL_HABILIDADE:
            partes.append(f"✨ Habilidade especial destravada: **{pet['habilidade_nome']}**!")

    def _somar_xp_extra(ganho_extra: int):
        dados_membro = xp_stats[membro.id]
        nivel_xp_antigo = dados_membro["nivel"]
        dados_membro["xp"] += ganho_extra
        dados_membro["nivel"], _, _ = _calcular_nivel(dados_membro["xp"])
        if dados_membro["nivel"] > nivel_xp_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados_membro["nivel"]))

    if venceu:
        chance_upar = _PET_CHANCE_UPAR_CRIATURA
        garantido = False
        if habilidade_ativa:
            if pet["habilidade_tipo"] == "chance_upar_extra":
                chance_upar += pet["habilidade_valor"]
            elif pet["habilidade_tipo"] == "upar_garantido":
                garantido = True
            elif pet["habilidade_tipo"] == "xp_flat_vitoria":
                ganho_extra = random.randint(*pet["habilidade_valor"])
                _somar_xp_extra(ganho_extra)
                partes.append(f"{pet['habilidade_nome']}: +`{ganho_extra}` XP extra pra {membro.mention}!")

        if garantido or random.random() < chance_upar:
            resultado_up = _pet_upar_criatura_aleatoria(membro.id)
            if resultado_up is not None:
                criatura_upada, nivel_criatura_novo, besta_nova, pet_novo_cascata = resultado_up
                partes.append(
                    f"🐾 **{pet['nome']}** ajudou **{criatura_upada['nome']}** ({membro.display_name}) a "
                    f"subir pro Nível de Capacidade `{nivel_criatura_novo}`!"
                )
                if besta_nova is not None and guild is not None:
                    asyncio.create_task(_anunciar_besta_desbloqueada(guild, membro, criatura_upada, besta_nova))
                if pet_novo_cascata is not None and guild is not None:
                    asyncio.create_task(_anunciar_pet_desbloqueado(guild, membro, criatura_upada, pet_novo_cascata))
    else:
        if habilidade_ativa and pet["habilidade_tipo"] == "xp_flat_derrota":
            ganho_extra = random.randint(*pet["habilidade_valor"])
            _somar_xp_extra(ganho_extra)
            partes.append(f"{pet['habilidade_nome']}: +`{ganho_extra}` XP de consolo pra {membro.mention}!")

    if partes:
        asyncio.create_task(_salvar_xp_stats())

    return "\n".join(partes) if partes else None


async def _pet_pos_boss_grupo(guild: discord.Guild, participantes: list, venceu: bool):
    """Roda `_pet_pos_boss` pra CADA participante de um confronto de Boss
    (uma batalha solo só passa uma lista de 1 elemento) e junta as notas de
    todo mundo num texto só, pronto pra encaixar no resultado."""
    notas = []
    for membro in participantes:
        nota = await _pet_pos_boss(guild, membro, venceu)
        if nota:
            notas.append(nota)
    return "\n".join(notas) if notas else None


# ══════════════════════════════════════════════════════════════════════
# .destravarbesta — comando de manutenção/correção. Verifica se a pessoa
# (ou alguém que o Reality aponte) tem alguma criatura ⚪/🔵/🟣 já no Nível
# de Capacidade máximo cuja Besta correspondente não foi concedida (por
# causa de alguma falha no desbloqueio automático em batalha) e concede na
# hora, anunciando no mesmo canal fixo de sempre (_BESTA_ANUNCIO_CANAL_ID).
# Idempotente: pode ser chamado várias vezes sem risco de duplicar — só
# concede enquanto sobrar Besta faltando no tier.
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="destravarbesta", aliases=["corrigirbesta", "checarbesta"])
async def cmd_destravarbesta(ctx, membro: discord.Member = None):
    """Corrige o bug de Besta não concedida/anunciada.
    Uso: .destravarbesta            → verifica você mesmo
         .destravarbesta @membro    → só o Reality pode checar outra pessoa
    """
    autor = ctx.author

    if membro is not None and membro.id != autor.id and autor.id != CRIADOR_ID:
        await ctx.send(
            "👽 **Renan:** ...você só pode checar as suas próprias criaturas."
        )
        return

    alvo = membro or autor

    dados = xp_stats[alvo.id]
    dados.setdefault("criaturas", [])

    candidatas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] in dados["criaturas"]
        and c["raridade"] in _BESTAS_POR_TIER
        and _nivel_criatura(alvo.id, c["id"]) >= _nivel_criatura_max(c["id"])
    ]

    if not candidatas:
        await ctx.send(
            f"👽 **Renan:** ...nenhuma criatura Comum, Rara ou Épica de "
            f"{alvo.mention} está no Nível de Capacidade máximo agora. Nada pra destravar."
        )
        return

    concedidas = []
    for criatura in candidatas:
        besta = _forcar_verificacao_besta(alvo.id, criatura)
        if besta is not None:
            concedidas.append((criatura, besta))

    if not concedidas:
        await ctx.send(
            f"👽 **Renan:** ...já verifiquei. {alvo.mention} já tem todas as Bestas "
            "disponíveis pros tiers das criaturas maxadas dela — nada faltando pra destravar."
        )
        return

    asyncio.create_task(_salvar_xp_stats())

    for criatura, besta in concedidas:
        if ctx.guild:
            asyncio.create_task(_anunciar_besta_desbloqueada(ctx.guild, alvo, criatura, besta))

    nomes = ", ".join(f"🐺 **{besta['nome']}**" for _, besta in concedidas)
    await ctx.send(
        f"✅ Corrigido! {alvo.mention} destravou: {nomes} — confira o canal de anúncios e `.criaturas`. ⚡"
    )


# ══════════════════════════════════════════════════════════════════════
# .destravarpet — comando de manutenção/correção. Verifica se a pessoa
# (ou alguém que o Reality aponte) tem alguma criatura 🔵 Rara já no Nível
# de Capacidade `_PET_NIVEL_DESBLOQUEIO` (4) ou mais cujo Pet correspondente
# não foi concedido (por causa de alguma falha no desbloqueio automático em
# batalha) e concede na hora, anunciando no mesmo canal fixo de sempre
# (_BESTA_ANUNCIO_CANAL_ID). Idempotente: pode ser chamado várias vezes sem
# risco de duplicar — só concede enquanto sobrar Pet faltando na coleção.
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="destravarpet", aliases=["corrigirpet", "checarpet"])
async def cmd_destravarpet(ctx, membro: discord.Member = None):
    """Corrige o bug de Pet não concedido/anunciado.
    Uso: .destravarpet            → verifica você mesmo
         .destravarpet @membro    → só o Reality pode checar outra pessoa
    """
    autor = ctx.author

    if membro is not None and membro.id != autor.id and autor.id != CRIADOR_ID:
        await ctx.send(
            "👽 **Renan:** ...você só pode checar as suas próprias criaturas."
        )
        return

    alvo = membro or autor

    dados = xp_stats[alvo.id]
    dados.setdefault("criaturas", [])

    candidatas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] in dados["criaturas"]
        and c["raridade"] == "raro"
        and _nivel_criatura(alvo.id, c["id"]) >= _PET_NIVEL_DESBLOQUEIO
    ]

    if not candidatas:
        await ctx.send(
            f"👽 **Renan:** ...nenhuma criatura Rara de "
            f"{alvo.mention} está no Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}` ou mais "
            "agora. Nada pra destravar."
        )
        return

    concedidos = []
    for criatura in candidatas:
        pet = _forcar_verificacao_pet(alvo.id, criatura)
        if pet is not None:
            concedidos.append((criatura, pet))

    if not concedidos:
        await ctx.send(
            f"👽 **Renan:** ...já verifiquei. {alvo.mention} já tem todos os Pets "
            "disponíveis pras criaturas Raras maxadas dela — nada faltando pra destravar."
        )
        return

    asyncio.create_task(_salvar_xp_stats())

    for criatura, pet in concedidos:
        if ctx.guild:
            asyncio.create_task(_anunciar_pet_desbloqueado(ctx.guild, alvo, criatura, pet))

    nomes = ", ".join(f"🐾 **{pet['nome']}**" for _, pet in concedidos)
    await ctx.send(
        f"✅ Corrigido! {alvo.mention} destravou: {nomes} — confira o canal de anúncios e `.equiparpet`. ⚡"
    )


# ══════════════════════════════════════════════════════════════════════
# .reiniciacriaturas — comando de manutenção. Zera a COLEÇÃO de criaturas
# de UMA pessoa específica (por ID): as criaturas/Bestas desbloqueadas, o
# Nível de Capacidade de cada uma e a criatura favorita ativa. NÃO mexe em
# XP, nível geral nem vitórias/derrotas — só no lado "criaturas" mesmo.
# Irreversível, por isso pede confirmação por botão antes de aplicar.
# ══════════════════════════════════════════════════════════════════════

class ReiniciarCriaturasView(discord.ui.View):
    def __init__(self, alvo_id: int, alvo_nome: str):
        super().__init__(timeout=60)
        self.alvo_id = alvo_id
        self.alvo_nome = alvo_nome

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != CRIADOR_ID:
            await interaction.response.send_message(
                "⚠️ Só o Reality pode confirmar esse reset.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="✅ Confirmar reset",
        style=discord.ButtonStyle.danger,
        custom_id="reiniciar_criaturas_confirmar"
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        dados = xp_stats[self.alvo_id]
        dados["criaturas"] = []
        dados["usos_criaturas"] = {}
        dados["favorito"] = {"id": None, "usos": 0, "cansacos": {}}

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=(
                f"♻️ **Criaturas de `{self.alvo_nome}` (`{self.alvo_id}`) reiniciadas** — "
                "coleção, Níveis de Capacidade e favorita voltaram a 0."
            ),
            embed=None,
            view=self
        )
        self.stop()
        asyncio.create_task(_salvar_xp_stats())

    @discord.ui.button(
        label="❌ Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="reiniciar_criaturas_cancelar"
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="❌ Reset cancelado.", embed=None, view=self)
        self.stop()


@bot.command(name="reiniciacriaturas", aliases=["reiniciarcriaturas", "resetcriaturas"])
async def cmd_reiniciacriaturas(ctx, alvo_id: int = None):
    """Reseta a coleção de criaturas (desbloqueadas, Níveis de Capacidade e
    favorita) de UMA pessoa específica, por ID. Não mexe em XP/nível geral
    nem vitórias/derrotas. Só o Reality pode usar.
    Uso: .reiniciacriaturas <ID do membro>"""
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.reiniciacriaturas <ID do membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    alvo = guild.get_member(alvo_id) if guild else None
    if alvo is None and guild:
        try:
            alvo = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            alvo = None

    alvo_nome = alvo.display_name if alvo else str(alvo_id)
    dados = xp_stats[alvo_id]
    qtd_criaturas = len(dados.get("criaturas", []))

    embed = discord.Embed(
        title="♻️ Reiniciar Criaturas",
        description=(
            f"👤 **Membro:** {alvo.mention if alvo else f'`{alvo_id}`'} — `{alvo_nome}`\n"
            f"📖 **Criaturas desbloqueadas atualmente:** `{qtd_criaturas}`\n\n"
            "Isso vai **zerar** a coleção de criaturas (inclusive 🐺 Bestas), o Nível de Capacidade "
            "de cada uma e a criatura favorita dessa pessoa.\n"
            "⚠️ XP, nível geral e vitórias/derrotas **não** são afetados — só o lado \"criaturas\".\n\n"
            "Tem certeza?"
        ),
        color=0xff4444
    )
    embed.set_footer(text="👽 Renan — Sistema de Criaturas")
    await ctx.send(embed=embed, view=ReiniciarCriaturasView(alvo_id, alvo_nome))


# ══════════════════════════════════════════════════════════════════════
# CRIATURA FAVORITA — comando `.favorito <nome>`. Enquanto alguém tiver uma
# favorita ativa, ela é SEMPRE a escolhida nas batalhas dessa pessoa (em vez
# do sorteio aleatório de sempre) — até "cansar" depois de um certo número
# de usos seguidos. Aí ela some da jogada, as batalhas voltam a sortear
# aleatoriamente, e a pessoa entra num cooldown até poder favoritar de novo.
# ══════════════════════════════════════════════════════════════════════

_FAVORITO_USOS_ATE_CANSAR = 5           # quantas batalhas seguidas usando a favorita até ela cansar
_FAVORITO_COOLDOWN_SEGUNDOS = 30 * 60   # 30 min de descanso depois de cansar, até poder favoritar de novo

_FAVORITO_PADRAO = {"id": None, "usos": 0, "cansacos": {}}


def _normalizar_texto(texto: str) -> str:
    """Tira acentos e baixa a caixa — deixa a comparação de nomes de
    criatura tolerante a 'kaiju do eco', 'Kaiju Do Eco', 'KAIJU DO ECO'..."""
    sem_acento = "".join(
        ch for ch in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(ch)
    )
    return sem_acento.lower().strip()


def _encontrar_criatura_por_nome(busca: str) -> dict:
    """Acha uma criatura em _BATALHA_CRIATURAS a partir de um nome digitado
    livremente (sem acento, com espaço, etc.). Tenta, nessa ordem: nome
    exato, id exato, e por fim uma busca por trecho (só aceita se achar
    UMA única criatura possível — em caso de ambiguidade, devolve None)."""
    alvo = _normalizar_texto(busca)
    if not alvo:
        return None

    for c in _BATALHA_CRIATURAS:
        if _normalizar_texto(c["nome"]) == alvo:
            return c

    alvo_id = alvo.replace(" ", "_")
    for c in _BATALHA_CRIATURAS:
        if c["id"] == alvo_id:
            return c

    candidatos = [c for c in _BATALHA_CRIATURAS if alvo in _normalizar_texto(c["nome"])]
    if len(candidatos) == 1:
        return candidatos[0]
    return None


def _favorito_status(user_id: int) -> dict:
    """Devolve o dict de favorito dessa pessoa, já garantindo a estrutura
    padrão e limpando sozinho qualquer cansaço cujo cooldown já tenha passado.
    Cada criatura cansada tem seu próprio tempo de descanso em "cansacos",
    então dá pra ter mais de uma "de castigo" ao mesmo tempo (ex: você troca
    de favorita antes da anterior acabar de descansar)."""
    dados = xp_stats[user_id]
    dados.setdefault("favorito", {"id": None, "usos": 0, "cansacos": {}})
    favorito = dados["favorito"]
    favorito.setdefault("id", None)
    favorito.setdefault("usos", 0)
    favorito.setdefault("cansacos", {})

    agora = time.time()
    expirados = [cid for cid, ate in favorito["cansacos"].items() if agora >= ate]
    for cid in expirados:
        del favorito["cansacos"][cid]

    return favorito


def _favorito_cooldown_restante(user_id: int, criatura_id: str) -> float:
    """Segundos restantes até UMA CRIATURA ESPECÍFICA poder ser favoritada de
    novo (0 se ela não estiver descansando no momento)."""
    favorito = _favorito_status(user_id)
    ate = favorito["cansacos"].get(criatura_id)
    if ate is None:
        return 0.0
    return max(0.0, ate - time.time())


def _formatar_tempo_restante(segundos: float) -> str:
    minutos, segs = divmod(max(0, int(segundos)), 60)
    return f"{minutos}m{segs:02d}s"


def _obter_criatura_favorita_ativa(user_id: int) -> dict:
    """Devolve a criatura favorita ATIVA dessa pessoa (não cansada), ou
    None se ela não tiver nenhuma favoritada no momento."""
    favorito = _favorito_status(user_id)
    if not favorito["id"]:
        return None
    return next((c for c in _BATALHA_CRIATURAS if c["id"] == favorito["id"]), None)


def _registrar_uso_favorito(user_id: int, criatura_id: str) -> bool:
    """Chamada toda vez que uma criatura é usada numa batalha. Se essa
    criatura for a favorita ativa dessa pessoa, soma +1 no contador de usos
    seguidos. Ao bater _FAVORITO_USOS_ATE_CANSAR, ela cansa: sai do posto de
    favorita (as próximas batalhas voltam a sortear aleatoriamente) e entra
    em cooldown até poder ser favoritada de novo. Devolve True se ela cansou
    JUSTO NESSE uso (pra poder avisar no resultado da batalha)."""
    favorito = _favorito_status(user_id)
    if favorito["id"] != criatura_id:
        return False
    favorito["usos"] += 1
    if favorito["usos"] >= _FAVORITO_USOS_ATE_CANSAR:
        favorito["cansacos"][criatura_id] = time.time() + _FAVORITO_COOLDOWN_SEGUNDOS
        favorito["id"] = None
        favorito["usos"] = 0
        return True
    return False


# 🐉 Míticos continuam raríssimos de desbloquear: não entram no sorteio
# normal de recompensa — só há uma checagem especial a cada N vitórias, com
# uma chance bem pequena de sair uma Mítica nova.
_MITICO_VITORIAS_INTERVALO = 10      # a cada quantas vitórias rola a chance de Mítica
_MITICO_CHANCE_DESBLOQUEIO = 0.01    # 1% de chance nessa rolagem

# 🦴 Fósseis — diferente do Mítico (que precisa de um MÚLTIPLO de vitórias),
# o Fóssil rola em TODA vitória, sem intervalo — mas só entra em jogo quando
# os dois lados da batalha (desafiante e desafiado) estão numa call de voz
# no momento em que ela acontece. Sem os dois em call, a rolagem nem
# acontece — não importa quantas vitórias a pessoa já tenha.
_FOSSIL_CHANCE_DESBLOQUEIO = 0.02     # 2% de chance nessa rolagem (só quando os dois estão em call)

_BATALHA_TEMPO_ACEITE = 60          # segundos que o desafiado tem pra aceitar/recusar
_BATALHA_TEMPO_SOMEM  = 60          # segundos até cada mensagem da batalha sumir sozinha

# ── Vantagem — comando .vantagem <ID>, só o Reality. Marca alguém pra
# GANHAR garantido a PRÓXIMA batalha que participar (como desafiante ou
# desafiado, tanto faz) e saquear entre _VANTAGEM_ROUBO_MIN e
# _VANTAGEM_ROUBO_MAX (20% a 30%) de XP garantido da outra pessoa — o
# percentual exato ainda é sorteado, só que dentro dessa faixa mais alta e
# sem chance de sair 0% — pulando o sorteio normal de vitória/roubo. É
# consumida (removida do set) assim que essa próxima batalha acontece. ──
_vantagem_ativa: set = set()      # user_ids com Vantagem pendente pra próxima batalha
_VANTAGEM_ROUBO_MIN = 0.20        # 20% — mínimo de xp roubado garantido quando a Vantagem é usada
_VANTAGEM_ROUBO_MAX = 0.30        # 30% — máximo de xp roubado garantido quando a Vantagem é usada
_VANTAGEM_ROUBO_TETO = 700        # teto máximo de XP roubado com a Vantagem — ainda travado,
                                    # mesmo sendo um roubo garantido, pra não ficar desigual
                                    # entre rank baixo e alto.

# ── Vantagem (call) — comando .vantagemfossio <ID>, só o Reality. Parecida
# com .vantagem (vitória garantida), mas com 3 diferenças:
#   1. Só "destrava" numa batalha em que desafiante e desafiado estejam os
#      dois na MESMA call no momento do combate. Se a próxima batalha dela
#      acontecer sem os dois em call juntos, a Vantagem NÃO é consumida —
#      fica pendente, esperando uma batalha em que a condição bata.
#   2. O roubo de XP usa uma faixa própria, mais baixa que a do .vantagem
#      normal: _VANTAGEM_FOSSIO_ROUBO_MIN a _MAX (10% a 20%, também sem
#      chance de sair 0%).
#   3. Como a condição já garante os dois em call, o desenterro de 🦴 Fóssil
#      (normalmente só _FOSSIL_CHANCE_DESBLOQUEIO = 2% de chance) sai
#      GARANTIDO nessa vitória também, se ainda sobrar algum Fóssil pra
#      quem venceu destravar. ──
_vantagem_fossio_ativa: set = set()   # user_ids com Vantagem (call) pendente
_VANTAGEM_FOSSIO_ROUBO_MIN = 0.10     # 10% — mínimo de xp roubado garantido com a Vantagem (call)
_VANTAGEM_FOSSIO_ROUBO_MAX = 0.20     # 20% — máximo de xp roubado garantido com a Vantagem (call)
_VANTAGEM_FOSSIO_ROUBO_TETO = 700     # teto máximo de XP roubado com a Vantagem (call) — mesmo teto do .vantagem normal


def _mesma_call(a: discord.Member, b: discord.Member) -> bool:
    """True se os dois estiverem conectados no mesmo canal de voz agora."""
    voz_a = a.voice.channel if a.voice else None
    voz_b = b.voice.channel if b.voice else None
    return voz_a is not None and voz_a == voz_b


async def _apagar_mensagem_depois(mensagem: discord.Message, segundos: int = _BATALHA_TEMPO_SOMEM) -> None:
    """Espera alguns segundos e apaga a mensagem sozinha, ignorando erros
    se ela já não existir mais (apagada, canal sumiu, etc.)."""
    await asyncio.sleep(segundos)
    try:
        await mensagem.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass


def _embed_status_desafio(
    desafiante: discord.Member, desafiado: discord.Member, estado: str
) -> discord.Embed:
    """Monta o embed do convite de desafio, num dos estados: pendente, aceito,
    recusado ou expirado."""
    if estado == "pendente":
        titulo = "⚔️ Um desafio foi lançado!"
        descricao = (
            f"👽 **Renan:** ...{desafiante.mention} desafiou {desafiado.mention} para uma batalha. "
            f"Eu aguardo a resposta. {desafiado.mention}, você aceita? Tem `{_BATALHA_TEMPO_ACEITE}s` "
            "pra decidir."
        )
        cor = 0x2b2b3b
    elif estado == "aceito":
        titulo = "✅ Desafio aceito!"
        descricao = (
            f"👽 **Renan:** ...{desafiado.mention} topou. A batalha vai começar. Eu testemunho o combate."
        )
        cor = 0x4bbf73
    elif estado == "recusado":
        titulo = "🏳️ Desafio recusado"
        descricao = (
            f"👽 **Renan:** ...{desafiado.mention} recuou. Eu respeito a escolha. Talvez na próxima, "
            f"{desafiante.mention}."
        )
        cor = 0x888888
    else:  # expirado
        titulo = "⌛ Desafio expirado"
        descricao = (
            f"👽 **Renan:** ...{desafiado.mention} não respondeu a tempo. O desafio se dissolve. "
            f"Talvez {desafiante.mention} tente de novo depois."
        )
        cor = 0x888888

    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text="👽 Renan — Arena de Batalhas")
    return embed


class DesafioView(discord.ui.View):
    """Botões de Aceitar/Recusar que aparecem no convite de desafio.
    Só o desafiado pode usá-los, e o convite expira sozinho depois de
    _BATALHA_TEMPO_ACEITE segundos se ninguém responder."""

    def __init__(self, desafiante: discord.Member, desafiado: discord.Member):
        super().__init__(timeout=_BATALHA_TEMPO_ACEITE)
        self.desafiante = desafiante
        self.desafiado = desafiado
        self.respondido = False
        self.mensagem: discord.Message = None  # setada logo após o send()

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="⚔️ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.desafiado.id:
            await interaction.response.send_message(
                "👽 **Renan:** ...esse desafio não é seu pra aceitar.", ephemeral=True
            )
            return

        self.respondido = True
        self._travar_botoes()
        await interaction.response.edit_message(
            embed=_embed_status_desafio(self.desafiante, self.desafiado, "aceito"),
            view=self,
        )
        self.stop()
        asyncio.create_task(_iniciar_batalha_apos_aceite(interaction.channel, self.desafiante, self.desafiado))

    @discord.ui.button(label="🏳️ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.desafiado.id:
            await interaction.response.send_message(
                "👽 **Renan:** ...esse desafio não é seu pra recusar.", ephemeral=True
            )
            return

        self.respondido = True
        self._travar_botoes()
        await interaction.response.edit_message(
            embed=_embed_status_desafio(self.desafiante, self.desafiado, "recusado"),
            view=self,
        )
        self.stop()
        _batalha_canal_ativo.discard(interaction.channel.id)

    async def on_timeout(self):
        if self.respondido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            await self.mensagem.edit(
                embed=_embed_status_desafio(self.desafiante, self.desafiado, "expirado"),
                view=self,
            )
        except discord.HTTPException:
            pass
        _batalha_canal_ativo.discard(self.mensagem.channel.id)


async def _iniciar_batalha_apos_aceite(
    canal: discord.TextChannel, desafiante: discord.Member, desafiado: discord.Member
) -> None:
    """Chamada quando o desafiado aceita — roda a batalha e, no final (ou em
    caso de erro), libera o canal pra um novo desafio poder ser lançado."""
    try:
        await _executar_batalha(canal, desafiante, desafiado)
    finally:
        _batalha_canal_ativo.discard(canal.id)


def _sortear_uma_criatura(user_id: int) -> dict:
    """Sorteia 1 criatura para essa pessoa invocar. Se ela tiver uma 🌟
    favorita ativa (e ainda não cansada), a favorita é SEMPRE a escolhida —
    sem sorteio nenhum. Só cai no sorteio aleatório (SOMENTE dentre as que
    ela já desbloqueou, ponderado pela raridade — Comuns saem com mais
    frequência que Raras, e assim por diante) quando não há favorita ativa."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))

    favorita = _obter_criatura_favorita_ativa(user_id)
    if favorita is not None and favorita["id"] in desbloqueadas:
        return favorita

    pool = [c for c in _BATALHA_CRIATURAS if c["id"] in desbloqueadas]
    if not pool:
        # segurança: nunca deveria cair aqui, já que _garantir_criaturas_iniciais
        # sempre concede as Comuns antes da batalha começar.
        pool = [c for c in _BATALHA_CRIATURAS if c["raridade"] == "comum"] or list(_BATALHA_CRIATURAS)
    pesos = [_RARIDADES[c["raridade"]]["peso"] for c in pool]
    return random.choices(pool, weights=pesos, k=1)[0]


def _sortear_criaturas(desafiante_id: int, desafiado_id: int):
    """Sorteia a criatura de cada lado da batalha, cada uma dentre APENAS o
    que aquela pessoa já tem desbloqueado — nunca uma criatura que ela ainda
    não possui."""
    return _sortear_uma_criatura(desafiante_id), _sortear_uma_criatura(desafiado_id)


async def _executar_batalha(
    canal: discord.TextChannel, desafiante: discord.Member, desafiado: discord.Member
) -> None:
    """Roda a sequência dramática da batalha inteira: abertura, revelação das
    duas criaturas, suspense e conclusão (com ou sem roubo de XP)."""
    criatura_desafiante, criatura_desafiado = _sortear_criaturas(desafiante.id, desafiado.id)

    # Nível de Capacidade (1 a 10) de cada criatura, PRA CADA pessoa — quanto
    # mais essa pessoa já batalhou com ela, mais alto o nível e mais forte
    # ela fica, mesmo entre criaturas da mesma raridade.
    nivel_desafiante = _nivel_criatura(desafiante.id, criatura_desafiante["id"])
    nivel_desafiado = _nivel_criatura(desafiado.id, criatura_desafiado["id"])

    # 🌟 Se a criatura sorteada é a favorita ativa de quem invocou, marca
    # visualmente — o sorteio já dá prioridade absoluta a ela em _sortear_uma_criatura.
    eh_favorita_desafiante = _favorito_status(desafiante.id)["id"] == criatura_desafiante["id"]
    eh_favorita_desafiado = _favorito_status(desafiado.id)["id"] == criatura_desafiado["id"]
    marcador_favorita_desafiante = " 🌟" if eh_favorita_desafiante else ""
    marcador_favorita_desafiado = " 🌟" if eh_favorita_desafiado else ""

    # 🌀 Booster de xp por Elemental — cada Elemental USADO nessa batalha
    # (convocado, ganhando ou perdendo, não importa) já concede na hora,
    # pra quem o convocou, um Booster de xp em dobro por
    # _ELEMENTAL_BOOSTER_MINUTOS minutos — empilha em cima de qualquer
    # booster que a pessoa já tiver ativo (mesma função do 🪙 Baú/.darbosster).
    boost_elemental_desafiante = criatura_desafiante["raridade"] == "elemental"
    boost_elemental_desafiado = criatura_desafiado["raridade"] == "elemental"
    if boost_elemental_desafiante:
        _conceder_xp_booster(desafiante.id, _ELEMENTAL_BOOSTER_MINUTOS)
    if boost_elemental_desafiado:
        _conceder_xp_booster(desafiado.id, _ELEMENTAL_BOOSTER_MINUTOS)
    marcador_elemental_desafiante = " 🌀✨" if boost_elemental_desafiante else ""
    marcador_elemental_desafiado = " 🌀✨" if boost_elemental_desafiado else ""

    # ── Abertura ──────────────────────────────────────────────────────────
    embed_abertura = discord.Embed(
        title="⚔️ UMA BATALHA COMEÇA!",
        description=(
            f"👽 **Renan:** ...{desafiante.mention} lançou o desafio. {desafiado.mention}, eu aguardo "
            "sua resposta. Todo mundo pra arena — isso vai ser interessante."
        ),
        color=0x2b2b3b,
    )
    embed_abertura.set_footer(text="👽 Renan — Arena de Batalhas")
    msg_abertura = await canal.send(embed=embed_abertura)
    asyncio.create_task(_apagar_mensagem_depois(msg_abertura))
    await asyncio.sleep(2)

    # ── Criatura do desafiante ───────────────────────────────────────────
    embed_c1 = discord.Embed(
        title="🔥 O desafiador entra em campo!",
        description=(
            f"**{desafiante.display_name}** invoca... **{criatura_desafiante['nome']}** "
            f"`⭐ Nível {nivel_desafiante}`{marcador_favorita_desafiante}{marcador_elemental_desafiante}!! 💥"
        ),
        color=0xff4444,
    )
    embed_c1.set_image(url=criatura_desafiante["gif"])
    msg_c1 = await canal.send(embed=embed_c1)
    asyncio.create_task(_apagar_mensagem_depois(msg_c1))
    await asyncio.sleep(2.5)

    # ── Criatura do desafiado ────────────────────────────────────────────
    embed_c2 = discord.Embed(
        title="💠 O desafiado revida!",
        description=(
            f"**{desafiado.display_name}** responde invocando... **{criatura_desafiado['nome']}** "
            f"`⭐ Nível {nivel_desafiado}`{marcador_favorita_desafiado}{marcador_elemental_desafiado}!! ⚡"
        ),
        color=0x4488ff,
    )
    embed_c2.set_image(url=criatura_desafiado["gif"])
    msg_c2 = await canal.send(embed=embed_c2)
    asyncio.create_task(_apagar_mensagem_depois(msg_c2))
    await asyncio.sleep(3)

    # ── Suspense antes do resultado ──────────────────────────────────────
    aviso = await canal.send("💥⚡ *As duas criaturas colidem em um choque de poder...* ⚡💥")
    await asyncio.sleep(2.5)
    try:
        await aviso.delete()
    except discord.HTTPException:
        pass

    # ── Sorteia o vencedor ────────────────────────────────────────────────
    # Combina a hierarquia de força das raridades com o Nível de Capacidade
    # de cada criatura (_chance_vitoria): quanto maior a diferença de
    # raridade E de nível, mais a balança pende pro lado mais forte — mas o
    # lado mais fraco sempre mantém uma chance real de dar a zebra.
    #
    # 🍀 EXCEÇÃO: se um dos dois tiver uma Vantagem pendente (.vantagem), ela
    # é consumida aqui e o resultado NEM passa pelo sorteio — essa pessoa
    # vence garantido essa batalha (a próxima que ela participar depois de
    # receber a Vantagem).
    vantagem_usada_por = None
    via_vantagem_fossio = False   # True quando quem venceu foi por causa do .vantagemfossio (não do .vantagem normal)
    if desafiante.id in _vantagem_ativa:
        _vantagem_ativa.discard(desafiante.id)
        vantagem_usada_por = desafiante.id
    elif desafiado.id in _vantagem_ativa:
        _vantagem_ativa.discard(desafiado.id)
        vantagem_usada_por = desafiado.id
    elif _mesma_call(desafiante, desafiado):
        # 🍀📞 Vantagem (call) — só entra em jogo se os dois estiverem
        # juntos numa call agora. Fora dessa condição fica pendente e cai
        # no sorteio normal, sem ser consumida.
        if desafiante.id in _vantagem_fossio_ativa:
            _vantagem_fossio_ativa.discard(desafiante.id)
            vantagem_usada_por = desafiante.id
            via_vantagem_fossio = True
        elif desafiado.id in _vantagem_fossio_ativa:
            _vantagem_fossio_ativa.discard(desafiado.id)
            vantagem_usada_por = desafiado.id
            via_vantagem_fossio = True

    if vantagem_usada_por == desafiante.id:
        vencedor, criatura_vencedora = desafiante, criatura_desafiante
        perdedor, criatura_perdedora = desafiado, criatura_desafiado
    elif vantagem_usada_por == desafiado.id:
        vencedor, criatura_vencedora = desafiado, criatura_desafiado
        perdedor, criatura_perdedora = desafiante, criatura_desafiante
    else:
        chance_desafiante_vence = _chance_vitoria(
            criatura_desafiante, nivel_desafiante, criatura_desafiado, nivel_desafiado
        )

        if random.random() < chance_desafiante_vence:
            vencedor, criatura_vencedora = desafiante, criatura_desafiante
            perdedor, criatura_perdedora = desafiado, criatura_desafiado
        else:
            vencedor, criatura_vencedora = desafiado, criatura_desafiado
            perdedor, criatura_perdedora = desafiante, criatura_desafiante

    # ── Registra o uso — CADA criatura usada nessa batalha (vencendo ou
    # perdendo) soma +1 no seu contador, e pode subir de Nível de Capacidade
    # na hora — quanto mais usada, mais forte ela fica com o tempo.
    nivel_antigo_criatura_vencedora, nivel_novo_criatura_vencedora = _registrar_uso_criatura(
        vencedor.id, criatura_vencedora["id"]
    )
    nivel_antigo_criatura_perdedora, nivel_novo_criatura_perdedora = _registrar_uso_criatura(
        perdedor.id, criatura_perdedora["id"]
    )

    # 🌟 Se alguma das duas era a favorita ativa de quem a usou, soma mais um
    # uso seguido nela também — e, se bater o limite, ela cansa aqui mesmo
    # (some da função de favorita e entra em cooldown).
    cansou_favorita_vencedora = _registrar_uso_favorito(vencedor.id, criatura_vencedora["id"])
    cansou_favorita_perdedora = _registrar_uso_favorito(perdedor.id, criatura_perdedora["id"])

    # ── Lança o "dado" que decide quanto (ou se) o vencedor rouba de XP ──
    dados_perdedor = xp_stats[perdedor.id]
    dados_vencedor = xp_stats[vencedor.id]
    xp_perdedor_antes = dados_perdedor["xp"]

    # ── Registro de vitórias/derrotas — atualiza sempre, independente de roubo de XP ──
    dados_vencedor["vitorias"] = dados_vencedor.get("vitorias", 0) + 1
    dados_perdedor["derrotas"] = dados_perdedor.get("derrotas", 0) + 1

    # ── Desbloqueio de criatura — como os dois só podem invocar criaturas que
    # JÁ possuem, a criatura usada na batalha nunca é nova pra quem venceu.
    # A recompensa da vitória é diferente: o vencedor tem chance de destravar
    # uma criatura NOVA (sorteada por raridade, dentre as que ainda não tem)
    # pra sua coleção. Quem perde não ganha nada disso.
    # 🐉 Míticas ficam de fora desse sorteio normal — elas têm uma checagem
    # especial própria logo abaixo, bem mais rara. 🌌 Secretas também ficam
    # de fora — essas só saem do 🪙 Baú (.bau), nunca como recompensa de
    # batalha. 🦴 Fósseis também ficam de fora — só saem com os dois lados em
    # call, ver checagem própria logo abaixo. 🐺 Bestas também ficam de fora —
    # essas só saem quando uma criatura Comum/Rara/Épica bate o Nível de
    # Capacidade máximo (ver _checar_desbloqueio_besta logo abaixo). ──
    dados_vencedor.setdefault("criaturas", [])
    _nao_possuidas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] not in dados_vencedor["criaturas"] and c["raridade"] not in ("mitico", "secreto", "fosseis", "bestas", "elemental")
    ]
    criatura_nova = None
    if _nao_possuidas:
        _pesos_novas = [_RARIDADES[c["raridade"]]["peso"] for c in _nao_possuidas]
        criatura_nova = random.choices(_nao_possuidas, weights=_pesos_novas, k=1)[0]
        dados_vencedor["criaturas"].append(criatura_nova["id"])

    # ── 🐉 Desbloqueio Mítico — só rola a cada _MITICO_VITORIAS_INTERVALO
    # vitórias do vencedor, e mesmo aí só com _MITICO_CHANCE_DESBLOQUEIO de
    # chance. São bestas absurdas (quase 99% de vitória contra qualquer
    # raridade menor; Mítico x Mítico é sorteio puro), então o jogo as torna
    # raríssimas de conseguir também. ──
    criatura_mitica_nova = None
    if (
        dados_vencedor["vitorias"] % _MITICO_VITORIAS_INTERVALO == 0
        and random.random() < _MITICO_CHANCE_DESBLOQUEIO
    ):
        _miticas_faltando = [
            c for c in _BATALHA_CRIATURAS
            if c["raridade"] == "mitico" and c["id"] not in dados_vencedor["criaturas"]
        ]
        if _miticas_faltando:
            criatura_mitica_nova = random.choice(_miticas_faltando)
            dados_vencedor["criaturas"].append(criatura_mitica_nova["id"])

    # ── 🦴 Desbloqueio de Fóssil — só entra em jogo quando os DOIS lados da
    # batalha (desafiante E desafiado) estão numa call de voz no exato
    # momento em que ela termina. Se essa condição bater, rola
    # _FOSSIL_CHANCE_DESBLOQUEIO de chance do vencedor desenterrar um Fóssil
    # novo — sem depender de vitórias acumuladas nem de intervalo nenhum,
    # diferente do Mítico. Se algum dos dois não estiver em call, a rolagem
    # nem acontece. ──
    criatura_fossil_nova = None
    _ambos_em_call = (
        desafiante.voice is not None and desafiante.voice.channel is not None
        and desafiado.voice is not None and desafiado.voice.channel is not None
    )
    if _ambos_em_call and (via_vantagem_fossio or random.random() < _FOSSIL_CHANCE_DESBLOQUEIO):
        # 📞 Se veio do .vantagemfossio, pula o sorteio de _FOSSIL_CHANCE_DESBLOQUEIO
        # (2%) e já cai direto aqui garantido — só depende de sobrar algum
        # Fóssil que quem venceu ainda não tenha.
        _fosseis_faltando = [
            c for c in _BATALHA_CRIATURAS
            if c["raridade"] == "fosseis" and c["id"] not in dados_vencedor["criaturas"]
        ]
        if _fosseis_faltando:
            criatura_fossil_nova = random.choice(_fosseis_faltando)
            dados_vencedor["criaturas"].append(criatura_fossil_nova["id"])

    # ── 🐺 Desbloqueio de Besta — vale pros dois lados, já que os dois
    # "usaram" sua criatura nessa batalha e qualquer uma das duas pode ter
    # batido o Nível de Capacidade máximo agora. Só concede quando a
    # criatura em questão é Comum, Rara ou Épica (as únicas com tier de
    # Besta associado) e o Nível máximo acabou de ser alcançado NESSA
    # batalha — ver _checar_desbloqueio_besta. ──
    besta_nova_vencedor = _checar_desbloqueio_besta(
        vencedor.id, criatura_vencedora, nivel_antigo_criatura_vencedora, nivel_novo_criatura_vencedora
    )
    besta_nova_perdedor = _checar_desbloqueio_besta(
        perdedor.id, criatura_perdedora, nivel_antigo_criatura_perdedora, nivel_novo_criatura_perdedora
    )

    # ── Anuncia no canal fixo (_BESTA_ANUNCIO_CANAL_ID) sempre que uma Besta
    # for destravada agora, dizendo quem foi e qual Besta. Vale pros dois
    # lados, já que qualquer um dos dois pode ter batido o nível máximo. ──
    if besta_nova_vencedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_besta_desbloqueada(canal.guild, vencedor, criatura_vencedora, besta_nova_vencedor)
        )
    if besta_nova_perdedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_besta_desbloqueada(canal.guild, perdedor, criatura_perdedora, besta_nova_perdedor)
        )

    # ── 🌀 Desbloqueio de Elemental — vale pros dois lados, já que os dois
    # "usaram" sua criatura nessa batalha e qualquer uma das duas pode ter
    # batido o Nível de Capacidade 6 agora. Só concede quando a criatura em
    # questão é 🟣 Épica e esse Nível 6 acabou de ser alcançado NESSA
    # batalha — ver _checar_desbloqueio_elemental. ──
    elemental_novo_vencedor = _checar_desbloqueio_elemental(
        vencedor.id, criatura_vencedora, nivel_antigo_criatura_vencedora, nivel_novo_criatura_vencedora
    )
    elemental_novo_perdedor = _checar_desbloqueio_elemental(
        perdedor.id, criatura_perdedora, nivel_antigo_criatura_perdedora, nivel_novo_criatura_perdedora
    )

    # ── Anuncia no canal fixo (_BESTA_ANUNCIO_CANAL_ID) sempre que um
    # Elemental for destravado agora, dizendo quem foi e qual Elemental. ──
    if elemental_novo_vencedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_elemental_desbloqueado(canal.guild, vencedor, criatura_vencedora, elemental_novo_vencedor)
        )
    if elemental_novo_perdedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_elemental_desbloqueado(canal.guild, perdedor, criatura_perdedora, elemental_novo_perdedor)
        )

    # ── Anuncia no canal fixo (_FOSSIL_ANUNCIO_CANAL_ID) sempre que um
    # Fóssil for desenterrado agora, mencionando quem foi e qual Fóssil. ──
    if criatura_fossil_nova is not None and canal.guild:
        asyncio.create_task(
            _anunciar_fossil_desbloqueado(canal.guild, vencedor, criatura_fossil_nova)
        )

    # ── 🐾 Desbloqueio de Pet — vale pros dois lados, pela mesma razão da
    # Besta acima: os dois "usaram" sua criatura nessa batalha, e qualquer
    # uma das duas pode ter batido o Nível de Capacidade 4 agora. Só
    # concede quando a criatura em questão é 🔵 Rara e esse Nível 4 acabou
    # de ser alcançado NESSA batalha — ver _checar_desbloqueio_pet. ──
    pet_novo_vencedor = _checar_desbloqueio_pet(
        vencedor.id, criatura_vencedora, nivel_antigo_criatura_vencedora, nivel_novo_criatura_vencedora
    )
    pet_novo_perdedor = _checar_desbloqueio_pet(
        perdedor.id, criatura_perdedora, nivel_antigo_criatura_perdedora, nivel_novo_criatura_perdedora
    )
    if pet_novo_vencedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_pet_desbloqueado(canal.guild, vencedor, criatura_vencedora, pet_novo_vencedor)
        )
    if pet_novo_perdedor is not None and canal.guild:
        asyncio.create_task(
            _anunciar_pet_desbloqueado(canal.guild, perdedor, criatura_perdedora, pet_novo_perdedor)
        )

    # ⚡ Golpe Especial — chance rara (_CHANCE_GOLPE_ESPECIAL) de aparecer nessa
    # batalha, sempre do lado de quem já venceu. Se a Vantagem foi usada, o
    # resultado já veio "arranjado" — golpe especial não entra em jogo aqui,
    # pra não misturar os dois sistemas.
    golpe_especial = _sortear_golpe_especial() if vantagem_usada_por is None else None

    xp_roubado = 0
    percentual = 0.0
    if vantagem_usada_por is not None:
        if via_vantagem_fossio:
            # 📞 Vantagem (call) usada — rouba entre 10% e 20% garantido
            # (sem chance de 0%), faixa própria e mais baixa que a do
            # .vantagem normal.
            percentual = random.uniform(_VANTAGEM_FOSSIO_ROUBO_MIN, _VANTAGEM_FOSSIO_ROUBO_MAX)
            teto_roubo = _VANTAGEM_FOSSIO_ROUBO_TETO
        else:
            # 🍀 Vantagem usada — rouba entre 20% e 30% garantido (sem chance de
            # 0%), sem passar pelo sorteio normal de "pode não roubar nada".
            percentual = random.uniform(_VANTAGEM_ROUBO_MIN, _VANTAGEM_ROUBO_MAX)
            teto_roubo = _VANTAGEM_ROUBO_TETO
        if xp_perdedor_antes > 0:
            xp_roubado = max(1, round(xp_perdedor_antes * percentual))
            xp_roubado = min(xp_roubado, xp_perdedor_antes, teto_roubo)  # nunca deixa o xp negativo, e trava no teto
    elif golpe_especial is not None and xp_perdedor_antes > 0:
        # ⚡ Golpe Especial ativo — ignora a chance de "não roubar nada" e usa
        # a faixa turbinada (_GOLPE_ESPECIAL_ROUBO_MIN / _MAX) em vez da normal.
        percentual = random.uniform(_GOLPE_ESPECIAL_ROUBO_MIN, _GOLPE_ESPECIAL_ROUBO_MAX)
        xp_roubado = max(1, round(xp_perdedor_antes * percentual))
        xp_roubado = min(xp_roubado, xp_perdedor_antes, _GOLPE_ESPECIAL_ROUBO_TETO)  # nunca deixa o xp negativo, e trava no teto
    elif xp_perdedor_antes > 0 and random.random() >= _BATALHA_CHANCE_SEM_ROUBO:
        percentual = random.uniform(_BATALHA_ROUBO_MIN, _BATALHA_ROUBO_MAX)
        xp_roubado = max(1, round(xp_perdedor_antes * percentual))
        xp_roubado = min(xp_roubado, xp_perdedor_antes, _BATALHA_ROUBO_TETO)  # nunca deixa o xp negativo, e trava no teto

    if xp_roubado > 0:
        nivel_antigo_vencedor = dados_vencedor["nivel"]

        dados_perdedor["xp"] = max(0, xp_perdedor_antes - xp_roubado)
        dados_perdedor["nivel"], _, _ = _calcular_nivel(dados_perdedor["xp"])

        dados_vencedor["xp"] += xp_roubado
        dados_vencedor["nivel"], _, _ = _calcular_nivel(dados_vencedor["xp"])

        if dados_vencedor["nivel"] > nivel_antigo_vencedor and canal.guild:
            asyncio.create_task(_anunciar_level_up(canal.guild, vencedor, dados_vencedor["nivel"]))

        asyncio.create_task(_atualizar_ranking_xp())

    # Salva sempre — mesmo sem roubo de XP, o placar de vitórias/derrotas mudou
    asyncio.create_task(_salvar_xp_stats())

    # ── Conclusão dramática — propositalmente usa o MESMO texto de sempre,
    # mesmo quando o resultado veio de uma Vantagem: ninguém no chat pode
    # perceber que essa batalha foi "arranjada". ──
    texto_golpe_especial = ""
    if golpe_especial is not None:
        texto_golpe_especial = (
            f"\n\n{golpe_especial['emoji']} **GOLPE ESPECIAL!!** **{criatura_vencedora['nome']}** usou "
            f"**{golpe_especial['nome']}** — {golpe_especial['frase']}! O saque de XP dessa vitória "
            "veio turbinado. ⚡"
        )

    if xp_roubado > 0:
        texto_roubo = (
            f"💰 O dado sorteou **`{percentual * 100:.1f}%`**! "
            f"**{vencedor.display_name}** saqueou **`{xp_roubado}` XP** de **{perdedor.display_name}**!"
            f"{texto_golpe_especial}"
        )
    else:
        texto_roubo = (
            f"🍃 O dado não favoreceu **{vencedor.display_name}** dessa vez — "
            f"nenhum XP foi roubado de **{perdedor.display_name}**."
        )

    texto_placar = (
        f"📊 **Retrospecto:** {vencedor.mention} `🏆 {dados_vencedor['vitorias']} vitórias / "
        f"{dados_vencedor['derrotas']} derrotas` — {perdedor.mention} `🏆 {dados_perdedor['vitorias']} vitórias / "
        f"{dados_perdedor['derrotas']} derrotas`"
    )

    partes_desbloqueio = []
    if criatura_nova is not None:
        info_raridade_nova = _RARIDADES[criatura_nova["raridade"]]
        partes_desbloqueio.append(
            f"🆕 De recompensa, **{vencedor.display_name}** desbloqueou "
            f"{info_raridade_nova['emoji']} **{criatura_nova['nome']}** "
            f"(*{info_raridade_nova['label']}*) na Enciclopédia! Use `.criaturas` pra conferir. 📖"
        )
    if criatura_mitica_nova is not None:
        info_raridade_mitica = _RARIDADES[criatura_mitica_nova["raridade"]]
        partes_desbloqueio.append(
            f"🐉✨ **SORTE RARÍSSIMA!!** Só {_MITICO_CHANCE_DESBLOQUEIO * 100:.0f}% de chance a cada "
            f"{_MITICO_VITORIAS_INTERVALO} vitórias, e **{vencedor.display_name}** acabou de desbloquear "
            f"{info_raridade_mitica['emoji']} **{criatura_mitica_nova['nome']}** "
            f"(*{info_raridade_mitica['label']}*)!! 🐉✨"
        )
    if criatura_fossil_nova is not None:
        info_raridade_fossil = _RARIDADES[criatura_fossil_nova["raridade"]]
        partes_desbloqueio.append(
            f"🦴✨ **ACHADO RARÍSSIMO!!** Os dois estavam numa call, e o dado só tinha "
            f"{_FOSSIL_CHANCE_DESBLOQUEIO * 100:.0f}% de chance — mas **{vencedor.display_name}** "
            f"desenterrou {info_raridade_fossil['emoji']} **{criatura_fossil_nova['nome']}** "
            f"(*{info_raridade_fossil['label']}*)!! 🦴✨"
        )
    if besta_nova_vencedor is not None:
        info_raridade_besta = _RARIDADES["bestas"]
        partes_desbloqueio.append(
            f"🐺⚡ **CONQUISTA!** A **{criatura_vencedora['nome']}** de {vencedor.display_name} chegou ao "
            f"**Nível de Capacidade máximo** e, como recompensa, {vencedor.display_name} desbloqueou "
            f"{info_raridade_besta['emoji']} **{besta_nova_vencedor['nome']}** "
            f"(*{info_raridade_besta['label']}*)!! 🐺⚡"
        )
    if besta_nova_perdedor is not None:
        info_raridade_besta = _RARIDADES["bestas"]
        partes_desbloqueio.append(
            f"🐺⚡ **CONQUISTA!** A **{criatura_perdedora['nome']}** de {perdedor.display_name} chegou ao "
            f"**Nível de Capacidade máximo** e, como recompensa, {perdedor.display_name} desbloqueou "
            f"{info_raridade_besta['emoji']} **{besta_nova_perdedor['nome']}** "
            f"(*{info_raridade_besta['label']}*)!! 🐺⚡"
        )
    if elemental_novo_vencedor is not None:
        info_raridade_elemental = _RARIDADES["elemental"]
        partes_desbloqueio.append(
            f"🌀⚡ **CONQUISTA!** A **{criatura_vencedora['nome']}** de {vencedor.display_name} chegou ao "
            f"**Nível de Capacidade `{_ELEMENTAL_NIVEL_DESBLOQUEIO}`** e, como recompensa, "
            f"{vencedor.display_name} desbloqueou {info_raridade_elemental['emoji']} "
            f"**{elemental_novo_vencedor['nome']}** (*{info_raridade_elemental['label']}*)!! 🌀⚡"
        )
    if elemental_novo_perdedor is not None:
        info_raridade_elemental = _RARIDADES["elemental"]
        partes_desbloqueio.append(
            f"🌀⚡ **CONQUISTA!** A **{criatura_perdedora['nome']}** de {perdedor.display_name} chegou ao "
            f"**Nível de Capacidade `{_ELEMENTAL_NIVEL_DESBLOQUEIO}`** e, como recompensa, "
            f"{perdedor.display_name} desbloqueou {info_raridade_elemental['emoji']} "
            f"**{elemental_novo_perdedor['nome']}** (*{info_raridade_elemental['label']}*)!! 🌀⚡"
        )
    if not partes_desbloqueio:
        partes_desbloqueio.append(
            f"🏅 **{vencedor.display_name}** já desbloqueou todas as criaturas normais existentes "
            "— só falta a sorte grande de alguma 🐉 Mítica agora!"
        )
    texto_desbloqueio = "\n\n".join(partes_desbloqueio)

    # ── Aviso de subida de Nível de Capacidade — vale pras duas criaturas,
    # a de quem venceu e a de quem perdeu, já que os dois "usaram" as suas. ──
    partes_nivel_criatura = []
    if nivel_novo_criatura_vencedora > nivel_antigo_criatura_vencedora:
        partes_nivel_criatura.append(
            f"📈 **{criatura_vencedora['nome']}** de {vencedor.display_name} ficou mais experiente "
            f"e subiu pro **⭐ Nível {nivel_novo_criatura_vencedora}**!"
        )
    if nivel_novo_criatura_perdedora > nivel_antigo_criatura_perdedora:
        partes_nivel_criatura.append(
            f"📈 **{criatura_perdedora['nome']}** de {perdedor.display_name} ficou mais experiente "
            f"e subiu pro **⭐ Nível {nivel_novo_criatura_perdedora}**!"
        )
    texto_nivel_criatura = ("\n\n" + "\n".join(partes_nivel_criatura)) if partes_nivel_criatura else ""

    # 🌟 Aviso de "cansaço" — se alguma das favoritas bateu o limite de usos
    # seguidos NESSA batalha, avisa que ela vai descansar e por quanto tempo.
    partes_favorita_cansada = []
    if cansou_favorita_vencedora:
        partes_favorita_cansada.append(
            f"😮‍💨 A favorita de **{vencedor.display_name}**, **{criatura_vencedora['nome']}**, cansou "
            f"depois de `{_FAVORITO_USOS_ATE_CANSAR}` usos seguidos! Vai descansar por "
            f"`{_FAVORITO_COOLDOWN_SEGUNDOS // 60} min` — as próximas batalhas voltam a sortear aleatoriamente."
        )
    if cansou_favorita_perdedora:
        partes_favorita_cansada.append(
            f"😮‍💨 A favorita de **{perdedor.display_name}**, **{criatura_perdedora['nome']}**, cansou "
            f"depois de `{_FAVORITO_USOS_ATE_CANSAR}` usos seguidos! Vai descansar por "
            f"`{_FAVORITO_COOLDOWN_SEGUNDOS // 60} min` — as próximas batalhas voltam a sortear aleatoriamente."
        )
    texto_favorita_cansada = ("\n\n" + "\n".join(partes_favorita_cansada)) if partes_favorita_cansada else ""

    # 🌀 Aviso de Booster de xp ativado — vale pra quem convocou um Elemental
    # nessa batalha, não importa se venceu ou perdeu (o booster já foi
    # concedido lá em cima, assim que os dois lados foram sorteados).
    partes_boost_elemental = []
    if boost_elemental_desafiante:
        partes_boost_elemental.append(
            f"🌀✨ **{desafiante.display_name}** convocou um Elemental e ativou um Booster de xp "
            f"(`x{_BAU_BOOSTER_MULTIPLICADOR}`, call e mensagem) por `{_ELEMENTAL_BOOSTER_MINUTOS} min`!"
        )
    if boost_elemental_desafiado:
        partes_boost_elemental.append(
            f"🌀✨ **{desafiado.display_name}** convocou um Elemental e ativou um Booster de xp "
            f"(`x{_BAU_BOOSTER_MULTIPLICADOR}`, call e mensagem) por `{_ELEMENTAL_BOOSTER_MINUTOS} min`!"
        )
    texto_boost_elemental = ("\n\n" + "\n".join(partes_boost_elemental)) if partes_boost_elemental else ""

    embed_resultado = discord.Embed(
        title="🏆 FIM DE BATALHA!",
        description=(
            f"**{criatura_vencedora['nome']}** `⭐ Nv.{nivel_novo_criatura_vencedora}` ({vencedor.mention}) derrota "
            f"**{criatura_perdedora['nome']}** `⭐ Nv.{nivel_novo_criatura_perdedora}` ({perdedor.mention})!\n\n"
            f"{texto_roubo}\n\n"
            f"{texto_desbloqueio}"
            f"{texto_nivel_criatura}"
            f"{texto_favorita_cansada}"
            f"{texto_boost_elemental}\n\n"
            f"{texto_placar}\n\n"
            f"👽 **Renan:** ...eu reconheço o vencedor. Foi uma boa batalha."
        ),
        color=0xf5c542,
        timestamp=discord.utils.utcnow(),
    )
    embed_resultado.set_thumbnail(url=vencedor.display_avatar.url)
    embed_resultado.set_footer(text="👽 Renan — Arena de Batalhas")
    msg_resultado = await canal.send(embed=embed_resultado)
    asyncio.create_task(_apagar_mensagem_depois(msg_resultado))

    # 📜 Log do RPG — só os ganhos orgânicos dessa batalha. Vale mesmo se uma
    # Vantagem foi usada nos bastidores: o log trata como uma vitória normal,
    # do mesmo jeito que o resto do bot já esconde isso do chat.
    partes_log = [
        f"⚔️ **{vencedor.display_name}** venceu **{perdedor.display_name}** num desafio "
        f"(**{criatura_vencedora['nome']}** vs **{criatura_perdedora['nome']}**)."
    ]
    if xp_roubado > 0:
        partes_log.append(
            f"💰 Saqueou **`{xp_roubado}` XP** (`{percentual * 100:.1f}%`) de **{perdedor.display_name}**."
        )
    if golpe_especial is not None:
        partes_log.append(f"{golpe_especial['emoji']} Golpe Especial: **{golpe_especial['nome']}**.")
    if criatura_nova is not None:
        info_r = _RARIDADES[criatura_nova["raridade"]]
        partes_log.append(
            f"🆕 **{vencedor.display_name}** desbloqueou {info_r['emoji']} **{criatura_nova['nome']}** "
            f"(*{info_r['label']}*)."
        )
    if criatura_mitica_nova is not None:
        info_r = _RARIDADES[criatura_mitica_nova["raridade"]]
        partes_log.append(
            f"🐉 **{vencedor.display_name}** desbloqueou o Mítico {info_r['emoji']} "
            f"**{criatura_mitica_nova['nome']}**!"
        )
    if criatura_fossil_nova is not None:
        info_r = _RARIDADES[criatura_fossil_nova["raridade"]]
        partes_log.append(
            f"🦴 **{vencedor.display_name}** desenterrou o Fóssil {info_r['emoji']} "
            f"**{criatura_fossil_nova['nome']}** (os dois estavam em call)!"
        )
    if besta_nova_vencedor is not None:
        partes_log.append(
            f"🐺 **{vencedor.display_name}** desbloqueou a Besta **{besta_nova_vencedor['nome']}** "
            "(Nível de Capacidade máximo)."
        )
    if besta_nova_perdedor is not None:
        partes_log.append(
            f"🐺 **{perdedor.display_name}** desbloqueou a Besta **{besta_nova_perdedor['nome']}** "
            "(Nível de Capacidade máximo)."
        )
    if elemental_novo_vencedor is not None:
        partes_log.append(
            f"🌀 **{vencedor.display_name}** desbloqueou o Elemental **{elemental_novo_vencedor['nome']}** "
            f"(Nível de Capacidade {_ELEMENTAL_NIVEL_DESBLOQUEIO})."
        )
    if elemental_novo_perdedor is not None:
        partes_log.append(
            f"🌀 **{perdedor.display_name}** desbloqueou o Elemental **{elemental_novo_perdedor['nome']}** "
            f"(Nível de Capacidade {_ELEMENTAL_NIVEL_DESBLOQUEIO})."
        )
    if boost_elemental_desafiante:
        partes_log.append(
            f"🌀✨ **{desafiante.display_name}** usou um Elemental e ganhou Booster de xp "
            f"(`x{_BAU_BOOSTER_MULTIPLICADOR}`) por {_ELEMENTAL_BOOSTER_MINUTOS} min."
        )
    if boost_elemental_desafiado:
        partes_log.append(
            f"🌀✨ **{desafiado.display_name}** usou um Elemental e ganhou Booster de xp "
            f"(`x{_BAU_BOOSTER_MULTIPLICADOR}`) por {_ELEMENTAL_BOOSTER_MINUTOS} min."
        )
    asyncio.create_task(_log_rpg(canal.guild, "⚔️ Batalha entre membros", "\n".join(partes_log)))


async def _processar_desafio(message: discord.Message) -> None:
    """Detecta 'eu te desafio @alguém' no chat e, se tudo certo, inicia a batalha.
    Só funciona dentro de CANAL_ARENA_RPG_ID — em qualquer outro canal, o Renan
    avisa que desafios só rolam ali e não deixa a batalha começar."""
    if message.guild is None or message.author.bot:
        return
    if not message.mentions:
        return
    if not _BATALHA_REGEX.search(message.content or ""):
        return

    if message.channel.id != CANAL_ARENA_RPG_ID:
        aviso = await message.channel.send(
            f"👽 **Renan:** ...desafios só valem em <#{CANAL_ARENA_RPG_ID}>. Leve essa briga pra lá."
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso, 10))
        return

    desafiante = message.author
    desafiado = next(
        (m for m in message.mentions if not m.bot and m.id != desafiante.id), None
    )

    if desafiado is None:
        await message.channel.send(
            "👽 **Renan:** ...não dá pra desafiar a si mesmo, nem um bot. Eu não aceito covardia."
        )
        return

    if message.channel.id in _batalha_canal_ativo:
        await message.channel.send(
            "👽 **Renan:** ...calma. Já tem uma batalha rolando por aqui, espere terminar."
        )
        return

    agora = time.time()
    ultimo = _batalha_ultimo_desafio.get(desafiante.id, 0)
    if agora - ultimo < _BATALHA_COOLDOWN_SEGUNDOS:
        restante = int(_BATALHA_COOLDOWN_SEGUNDOS - (agora - ultimo))
        await message.channel.send(
            f"👽 **Renan:** ...ainda descanso do último combate. "
            f"Espere mais `{restante}s` antes de desafiar de novo."
        )
        return

    guild = message.guild
    cargo_xp = guild.get_role(CARGO_XP_ID)
    if not cargo_xp or cargo_xp not in desafiante.roles or cargo_xp not in desafiado.roles:
        await message.channel.send(
            "👽 **Renan:** ...pra batalhar valendo pontos, os dois precisam estar "
            "participando do ranking de nível."
        )
        return

    dados_desafiante = xp_stats[desafiante.id]
    dados_desafiado = xp_stats[desafiado.id]
    if dados_desafiante["xp"] <= 0 and dados_desafiado["xp"] <= 0:
        await message.channel.send(
            "👽 **Renan:** ...ninguém aqui tem XP suficiente pra valer a pena essa batalha ainda."
        )
        return

    _batalha_ultimo_desafio[desafiante.id] = agora
    _batalha_canal_ativo.add(message.channel.id)

    view = DesafioView(desafiante, desafiado)
    convite = await message.channel.send(
        embed=_embed_status_desafio(desafiante, desafiado, "pendente"), view=view
    )
    view.mensagem = convite
    asyncio.create_task(_apagar_mensagem_depois(convite))

# ══════════════════════════════════════════════════════════════════════


CANAL_CRIATURAS_ID = 1536880856743022682  # canal onde a coleção do .criaturas é SEMPRE enviada


@bot.command(name="criaturas")
async def cmd_criaturas(ctx, membro: discord.Member = None):
    """Mostra a coleção de criaturas desbloqueadas de alguém na Arena de
    Batalhas (ou de quem usou o comando, se ninguém for mencionado).
    A resposta é sempre jogada no canal CANAL_CRIATURAS_ID, não importa
    de onde o comando foi chamado.
    Uso: .criaturas [@alguém]"""
    alvo = membro or ctx.author
    desbloqueadas = set(_garantir_criaturas_iniciais(alvo.id))
    favorito_alvo = _favorito_status(alvo.id)

    if favorito_alvo["id"]:
        criatura_favorita = next((c for c in _BATALHA_CRIATURAS if c["id"] == favorito_alvo["id"]), None)
        nome_favorita = criatura_favorita["nome"] if criatura_favorita else favorito_alvo["id"]
        linha_favorito = (
            f"🌟 **Favorita atual:** {nome_favorita} "
            f"(`{favorito_alvo['usos']}/{_FAVORITO_USOS_ATE_CANSAR}` usos até cansar)"
        )
    elif favorito_alvo["cansacos"]:
        partes_descanso = []
        for cid, ate in favorito_alvo["cansacos"].items():
            c_cansada = next((c for c in _BATALHA_CRIATURAS if c["id"] == cid), None)
            nome_cansada = c_cansada["nome"] if c_cansada else cid
            partes_descanso.append(f"**{nome_cansada}** (`{_formatar_tempo_restante(ate - time.time())}`)")
        linha_favorito = (
            "😮‍💨 Descansando: " + ", ".join(partes_descanso) +
            " — mas dá pra favoritar outra criatura a qualquer momento com `.favorito <nome>`."
        )
    else:
        linha_favorito = "🌟 *Sem favorita ativa no momento — use `.favorito <nome>` pra escolher uma.*"

    embed = discord.Embed(
        title=f"📖 Coleção de Criaturas — {alvo.display_name}",
        description=(
            f"🔓 **{len(desbloqueadas)}/{len(_BATALHA_CRIATURAS)}** criaturas desbloqueadas até agora!\n"
            "Vença batalhas invocando as que faltam pra completar a coleção. ⚔️\n"
            "⭐ *O número ao lado do nome é o Nível de Capacidade dela — sobe até 10 "
            "quanto mais você invoca essa criatura em batalha.*\n\n"
            f"{linha_favorito}"
        ),
        color=0x9b59b6,
    )

    for raridade in _ORDEM_RARIDADES:
        info = _RARIDADES[raridade]
        linhas = []
        for c in _BATALHA_CRIATURAS:
            if c["raridade"] != raridade:
                continue
            if c["id"] in desbloqueadas:
                nivel = _nivel_criatura(alvo.id, c["id"])
                marcador = " 🌟" if favorito_alvo["id"] == c["id"] else ""
                linhas.append(f"🔓 {c['nome']} `⭐ Nv.{nivel}`{marcador}")
            else:
                linhas.append(f"🔒 {c['nome']}")
        if linhas:
            embed.add_field(name=f"{info['emoji']} {info['label']}", value="\n".join(linhas), inline=False)

    pets_desbloqueados = set(_pets_desbloqueados(alvo.id))
    pet_equipado_id = xp_stats[alvo.id].get("pet_equipado")
    linhas_pets = []
    for p in _PETS:
        if p["id"] in pets_desbloqueados:
            nivel_pet_atual = _nivel_pet(alvo.id, p["id"])
            marcador = " 🐾*(equipado)*" if p["id"] == pet_equipado_id else ""
            linhas_pets.append(f"🔓 {p['nome']} `⭐ Nv.{nivel_pet_atual}/{_PET_NIVEL_MAX}`{marcador}")
        else:
            linhas_pets.append(f"🔒 {p['nome']}")
    embed.add_field(
        name=f"🐾 Pets ({len(pets_desbloqueados)}/{len(_PETS)})",
        value=(
            "\n".join(linhas_pets) + "\n\n"
            "*Desbloqueados ao levar uma criatura 🔵 Rara até o Nível de Capacidade "
            f"`{_PET_NIVEL_DESBLOQUEIO}`. Equipe um com `.equiparpet <nome>` — eles dão bônus na "
            "chance de vencer Boss e ajudam a upar suas criaturas!*"
        ),
        inline=False,
    )

    embed.add_field(
        name="⚡ Golpes Especiais",
        value=(
            f"De vez em quando (`{_CHANCE_GOLPE_ESPECIAL * 100:.0f}%` de chance), no meio de um "
            "**\"eu te desafio @alguém\"**, a criatura vencedora solta um **Golpe Especial** — um ataque "
            "raro e nomeado (tipo 🌑 *Investida das Sombras* ou 🔥 *Chama Ancestral*) que turbina o saque "
            f"de XP daquela vitória pra entre `{_GOLPE_ESPECIAL_ROUBO_MIN * 100:.0f}%` e "
            f"`{_GOLPE_ESPECIAL_ROUBO_MAX * 100:.0f}%`, bem acima do normal!\n"
            "É sorte pura — qualquer criatura, de qualquer raridade ou nível, pode puxar um a qualquer momento. 🎲"
        ),
        inline=False,
    )

    embed.set_thumbnail(url=alvo.display_avatar.url)
    embed.set_footer(text="👽 Renan — confira também a 📖 Enciclopédia no canal de ranking")

    canal_destino = bot.get_channel(CANAL_CRIATURAS_ID)
    if canal_destino is None:
        # Canal não encontrado (bot fora do servidor certo, canal deletado etc.)
        # — cai pro canal onde o comando foi chamado, pra não perder a resposta.
        await ctx.send(embed=embed)
        return

    await canal_destino.send(embed=embed)
    if ctx.channel.id != canal_destino.id:
        await ctx.send(f"📖 Sua coleção foi enviada em {canal_destino.mention}!")


# ══════════════════════════════════════════════════════════════════════
# COMANDO .favorito — escolhe uma criatura favorita pras batalhas. Enquanto
# ela estiver ativa, é SEMPRE ela quem entra em campo (sem sorteio) — até
# cansar depois de _FAVORITO_USOS_ATE_CANSAR usos seguidos, quando então
# some por _FAVORITO_COOLDOWN_SEGUNDOS antes de poder ser favoritada de novo.
# ══════════════════════════════════════════════════════════════════════

_FAVORITO_PALAVRAS_REMOVER = {"remover", "limpar", "cancelar", "nenhum", "nenhuma", "tirar"}


@bot.command(name="favorito", aliases=["usarmonstro", "monstrofavorito"])
async def cmd_favorito(ctx, *, nome: str = None):
    """Define (ou consulta) sua criatura favorita pra batalhas.
    Uso:
      .favorito <nome da criatura>  → define a favorita (ela passa a entrar em TODA batalha sua)
      .favorito                     → mostra o status atual (favorita ativa ou tempo de cansaço restante)
      .favorito remover             → tira a favorita atual, sem precisar esperar ela cansar
    """
    autor = ctx.author
    favorito = _favorito_status(autor.id)

    # ── Sem argumento nenhum: só mostra o status atual ──────────────────
    if nome is None:
        if favorito["id"]:
            criatura_atual = next((c for c in _BATALHA_CRIATURAS if c["id"] == favorito["id"]), None)
            nome_atual = criatura_atual["nome"] if criatura_atual else favorito["id"]
            nivel_atual = _nivel_criatura(autor.id, favorito["id"])
            await ctx.send(
                f"👽 **Renan:** Sua favorita agora é **{nome_atual}** `⭐ Nv.{nivel_atual}`. "
                f"Já foi usada `{favorito['usos']}/{_FAVORITO_USOS_ATE_CANSAR}` vezes seguidas até cansar."
            )
        elif favorito["cansacos"]:
            partes = []
            for cid, ate in favorito["cansacos"].items():
                c_cansada = next((c for c in _BATALHA_CRIATURAS if c["id"] == cid), None)
                nome_cansada = c_cansada["nome"] if c_cansada else cid
                partes.append(f"**{nome_cansada}** (`{_formatar_tempo_restante(ate - time.time())}`)")
            await ctx.send(
                "👽 **Renan:** ...você não tem favorita ativa agora. Descansando: "
                + ", ".join(partes) +
                ". Pode favoritar outra criatura a qualquer momento com `.favorito <nome>`."
            )
        else:
            await ctx.send(
                "👽 **Renan:** ...você não tem nenhuma favorita agora — suas batalhas estão "
                "sorteando aleatoriamente. Use `.favorito <nome da criatura>` pra escolher uma."
            )
        return

    # ── Remover a favorita atual, sem precisar esperar cansar ───────────
    if _normalizar_texto(nome) in _FAVORITO_PALAVRAS_REMOVER:
        if not favorito["id"]:
            await ctx.send("👽 **Renan:** ...você já não tinha nenhuma favorita ativa.")
            return
        favorito["id"] = None
        favorito["usos"] = 0
        asyncio.create_task(_salvar_xp_stats())
        await ctx.send(
            "👽 **Renan:** ...favorita removida. Suas batalhas voltam a sortear livremente."
        )
        return

    # ── Encontra a criatura pelo nome digitado ───────────────────────────
    criatura = _encontrar_criatura_por_nome(nome)
    if criatura is None:
        await ctx.send(
            f"⚠️ Não encontrei nenhuma criatura chamada `{nome}`. Confira o nome certinho com `.criaturas`."
        )
        return

    desbloqueadas = set(_garantir_criaturas_iniciais(autor.id))
    if criatura["id"] not in desbloqueadas:
        await ctx.send(
            f"👽 **Renan:** ...você ainda não desbloqueou **{criatura['nome']}**. "
            "Só dá pra favoritar quem já tá na sua coleção — confira com `.criaturas`."
        )
        return

    # ── Só bloqueia se for JUSTO a criatura que ainda tá descansando — pode
    # trocar por QUALQUER OUTRA livremente, mesmo com essa ainda de castigo ──
    cansaco_ate = favorito["cansacos"].get(criatura["id"])
    if cansaco_ate is not None:
        restante = _formatar_tempo_restante(cansaco_ate - time.time())
        await ctx.send(
            f"👽 **Renan:** ...**{criatura['nome']}** ainda está descansando. Espere mais "
            f"`{restante}` antes de favoritá-la de novo — ou escolha outra com `.favorito <nome>`."
        )
        return

    favorito["id"] = criatura["id"]
    favorito["usos"] = 0
    asyncio.create_task(_salvar_xp_stats())

    info_raridade = _RARIDADES[criatura["raridade"]]
    nivel_atual = _nivel_criatura(autor.id, criatura["id"])
    await ctx.send(
        f"👽 **Renan:** ...pronto. {info_raridade['emoji']} **{criatura['nome']}** `⭐ Nv.{nivel_atual}` "
        f"agora é sua favorita — ela vai entrar em TODA batalha sua a partir de agora, até usar "
        f"`{_FAVORITO_USOS_ATE_CANSAR}` vezes seguidas e precisar descansar. Escolha bem."
    )


# ══════════════════════════════════════════════════════════════════════
# COMANDO .equiparpet — escolhe qual Pet fica ATIVO (equipado) pra dar
# suporte nas batalhas contra Boss. Só um Pet por vez; trocar de Pet NÃO
# zera o progresso de Nível dele (fica salvo por Pet, igual o Nível de
# Capacidade das criaturas) — só o Pet equipado no momento é quem soma o
# bônus de chance contra Boss e ajuda a upar criaturas.
# ══════════════════════════════════════════════════════════════════════

_PET_PALAVRAS_REMOVER = {"remover", "limpar", "cancelar", "nenhum", "nenhuma", "tirar", "desequipar"}


@bot.command(name="equiparpet", aliases=["pet", "usarpet", "meupet"])
async def cmd_equiparpet(ctx, *, nome: str = None):
    """Equipa (ou consulta) seu Pet ativo pras batalhas contra Boss.
    Uso:
      .equiparpet <nome do pet>  → equipa esse Pet (precisa já tê-lo desbloqueado)
      .equiparpet                → mostra o Pet equipado agora (ou sua lista de Pets, se nenhum)
      .equiparpet remover        → desequipa, sem trocar por outro
    """
    autor = ctx.author
    pets_possuidos = _pets_desbloqueados(autor.id)

    # ── Sem argumento nenhum: só mostra o status atual ───────────────────
    if nome is None:
        pet_atual = _obter_pet_equipado(autor.id)
        if pet_atual:
            nivel_atual = _nivel_pet(autor.id, pet_atual["id"])
            bonus = _pet_bonus_chance_boss(autor.id) * 100
            linha_habilidade = (
                f"✨ Habilidade **{pet_atual['habilidade_nome']}** já ativa!"
                if nivel_atual >= _PET_NIVEL_HABILIDADE
                else f"🔒 Habilidade **{pet_atual['habilidade_nome']}** destrava no Nível `{_PET_NIVEL_HABILIDADE}`."
            )
            await ctx.send(
                f"🐾 Seu Pet equipado agora é **{pet_atual['nome']}** `Nv.{nivel_atual}/{_PET_NIVEL_MAX}` — "
                f"soma `+{bonus:.1f}%` na chance de vencer Boss.\n{linha_habilidade}"
            )
        elif pets_possuidos:
            nomes = ", ".join(
                f"**{p['nome']}** `Nv.{_nivel_pet(autor.id, p['id'])}`"
                for p in _PETS if p["id"] in pets_possuidos
            )
            await ctx.send(
                f"👽 **Renan:** ...você tem Pets, mas nenhum equipado agora. Seus Pets: {nomes}. "
                "Use `.equiparpet <nome>` pra escolher um."
            )
        else:
            await ctx.send(
                "👽 **Renan:** ...você ainda não tem nenhum Pet. Leve uma criatura 🔵 Rara até o "
                f"Nível de Capacidade `{_PET_NIVEL_DESBLOQUEIO}` em batalhas — tem chance dela render um Pet de graça."
            )
        return

    # ── Desequipar, sem trocar por outro ──────────────────────────────
    if _normalizar_texto(nome) in _PET_PALAVRAS_REMOVER:
        dados = xp_stats[autor.id]
        if not dados.get("pet_equipado"):
            await ctx.send("👽 **Renan:** ...você já não tinha nenhum Pet equipado.")
            return
        dados["pet_equipado"] = None
        asyncio.create_task(_salvar_xp_stats())
        await ctx.send("👽 **Renan:** ...Pet desequipado. Nenhum bônus de suporte ativo agora.")
        return

    # ── Equipar um Pet específico ─────────────────────────────────────
    pet = _encontrar_pet_por_nome(nome)
    if pet is None:
        await ctx.send(f"⚠️ Não encontrei nenhum Pet chamado `{nome}`. Confira o nome certinho.")
        return

    if pet["id"] not in pets_possuidos:
        await ctx.send(
            f"👽 **Renan:** ...você ainda não desbloqueou **{pet['nome']}**. "
            "Só dá pra equipar Pets que já são seus."
        )
        return

    dados = xp_stats[autor.id]
    dados["pet_equipado"] = pet["id"]
    asyncio.create_task(_salvar_xp_stats())

    nivel_atual = _nivel_pet(autor.id, pet["id"])
    await ctx.send(
        f"🐾 **{pet['nome']}** `Nv.{nivel_atual}/{_PET_NIVEL_MAX}` equipado!! 😆✨ Ele vai te ajudar "
        "nas próximas batalhas contra Boss — vença ou perca, ele sobe de Nível junto com você."
    )


# ══════════════════════════════════════════════════════════════════════
# .darcriatura — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Concede uma criatura específica (por nome) direto pra coleção de alguém,
# sem precisar passar por batalha nem sorteio. Útil pra corrigir coleção,
# testar raridades específicas ou repor algo perdido.
# De propósito NÃO aparece em nenhum lugar do help/ajuda.
# Uso (PV ou servidor): .darcriatura <nome da criatura> <ID do membro>
# Exemplo: .darcriatura Kraken do Abismo 769951556388257812
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="darcriatura")
async def cmd_darcriatura(ctx, *, texto: str = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if texto is None:
        aviso = await ctx.send("⚠️ Uso: `.darcriatura <nome da criatura> <ID do membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    # O ID precisa ser o ÚLTIMO token da mensagem — tudo antes disso é o
    # nome da criatura (que pode ter espaço, acento, etc.).
    partes = texto.rsplit(" ", 1)
    if len(partes) != 2 or not partes[1].isdigit():
        aviso = await ctx.send(
            "⚠️ Uso: `.darcriatura <nome da criatura> <ID do membro>`\n"
            "O ID precisa vir por último, separado por espaço. "
            "Exemplo: `.darcriatura Kraken do Abismo 769951556388257812`"
        )
        await _apagar_mensagem_depois(aviso, 15)
        return

    nome_criatura, alvo_id_texto = partes
    alvo_id = int(alvo_id_texto)

    criatura = _encontrar_criatura_por_nome(nome_criatura)
    if criatura is None:
        aviso = await ctx.send(
            f"❌ Nenhuma criatura encontrada pra `{nome_criatura}` (ou o nome é ambíguo — "
            "tenta ser mais específico)."
        )
        await _apagar_mensagem_depois(aviso, 15)
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    alvo = guild.get_member(alvo_id) if guild else None
    if alvo is None and guild:
        try:
            alvo = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            alvo = None
    alvo_nome = alvo.display_name if alvo else str(alvo_id)

    dados = xp_stats[alvo_id]
    dados.setdefault("criaturas", [])
    info_raridade = _RARIDADES[criatura["raridade"]]

    if criatura["id"] in dados["criaturas"]:
        aviso = await ctx.send(
            f"⚠️ `{alvo_nome}` já tem {info_raridade['emoji']} **{criatura['nome']}** — nada mudou."
        )
        await _apagar_mensagem_depois(aviso, 15)
        return

    dados["criaturas"].append(criatura["id"])
    asyncio.create_task(_salvar_xp_stats())

    confirmacao = await ctx.send(
        f"✅ {info_raridade['emoji']} **{criatura['nome']}** (*{info_raridade['label']}*) concedida "
        f"pra `{alvo_nome}` (`{alvo_id}`)."
    )
    await _apagar_mensagem_depois(confirmacao, 15)


# ══════════════════════════════════════════════════════════════════════
# .uparcriatura — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Sobe em 1 o Nível de Capacidade da criatura favorita/equipada de alguém
# (a mesma lógica de _calcular_nivel_criatura / _NIVEL_CRIATURA_USOS_ACUMULADOS
# usada pelo resto do sistema — só que "empurrando" os usos direto pro
# limiar do próximo nível, em vez de esperar batalhas de verdade).
# De propósito NÃO aparece em nenhum lugar do help/ajuda.
# Uso (PV ou servidor): .uparcriatura <ID ou @membro>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="uparcriatura")
async def cmd_uparcriatura(ctx, alvo_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.uparcriatura <ID ou @membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    criatura = _obter_criatura_favorita_ativa(alvo_id)
    if criatura is None:
        aviso = await ctx.send(f"❌ `{alvo_id}` não tem criatura favorita/equipada no momento.")
        await _apagar_mensagem_depois(aviso, 15)
        return

    criatura_id = criatura["id"]
    teto = _nivel_criatura_max(criatura_id)
    nivel_atual = _nivel_criatura(alvo_id, criatura_id)

    if nivel_atual >= teto:
        aviso = await ctx.send(f"⚠️ `{criatura['nome']}` já está no nível máximo (`{teto}`).")
        await _apagar_mensagem_depois(aviso, 15)
        return

    tabela = (
        _NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO
        if criatura_id in _NIVEL_CRIATURA_MAX_ESPECIAL
        else _NIVEL_CRIATURA_USOS_ACUMULADOS
    )
    dados = xp_stats[alvo_id]
    dados.setdefault("usos_criaturas", {})
    dados["usos_criaturas"][criatura_id] = max(
        dados["usos_criaturas"].get(criatura_id, 0),
        tabela[nivel_atual],   # limiar de usos mínimos pro PRÓXIMO nível
    )
    nivel_novo = _calcular_nivel_criatura(dados["usos_criaturas"][criatura_id], criatura_id)
    asyncio.create_task(_salvar_xp_stats())

    confirmacao = await ctx.send(f"✅ `{criatura['nome']}` (`{alvo_id}`) → Nível `{nivel_novo}`.")
    await _apagar_mensagem_depois(confirmacao, 15)


# ══════════════════════════════════════════════════════════════════════
# BAÚ — evento de recompensa surpresa
# Comando .bau (só o Reality/CRIADOR_ID pode ativar) joga um baú com botão
# no canal _BAU_CANAL_ID. A PRIMEIRA pessoa que clicar leva o prêmio: na
# maioria das vezes um % de XP a mais (sorteado entre 1% e 20% do XP atual
# dela); mais raro um booster de 5 minutos que DOBRA o xp ganho em call e
# em mensagem nesse período; e, RARÍSSIMO (o prêmio mais difícil de todos),
# uma criatura de raridade 🌌 Secreta — a única forma de conseguir uma.
#
# .baumimic joga um baú visualmente IDÊNTICO, mas que é, na verdade, um
# Mimic disfarçado: quem clicar primeiro cai numa armadilha e PERDE entre
# _BAU_MIMIC_XP_MIN e _BAU_MIMIC_XP_MAX do XP dela, em vez de ganhar algo.
# ══════════════════════════════════════════════════════════════════════

_BAU_GIF = "https://static2.klipy.com/ii/d7aec6f6f171607374b2065c836f92f4/be/e0/WQOIGADT.gif"
_BAU_CANAL_ID = 1501260061530390563  # canal de anúncios do RPG

_BAU_CHANCE_SECRETO = 0.08    # 8% de chance — ainda o prêmio mais raro do baú (o booster é 15%), uma criatura 🌌 Secreta
_BAU_CHANCE_BOOSTER = 0.15    # 15% de chance de sair o booster
_BAU_XP_MIN = 0.01            # 1%  — mínimo de xp que o dado pode sortear
_BAU_XP_MAX = 0.20            # 20% — máximo de xp que o dado pode sortear
_BAU_XP_TETO = 800            # teto máximo de XP por baú — evita que rank alto dispare
                                # cada vez mais na frente do rank baixo.
_BAU_BOOSTER_MINUTOS = 5
_BAU_BOOSTER_MULTIPLICADOR = 2

_BAU_MIMIC_GIF = "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/c105ac18-b254-4cb1-9e1d-eb83be6b6939/df17unu-65c15ff8-39f7-4a3a-b865-14090f46e4c5.gif?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiIvZi9jMTA1YWMxOC1iMjU0LTRjYjEtOWUxZC1lYjgzYmU2YjY5MzkvZGYxN3VudS02NWMxNWZmOC0zOWY3LTRhM2EtYjg2NS0xNDA5MGY0NmU0YzUuZ2lmIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.QfbOzXs4HatDKEoHtYg_R2SEZ_jSZkyFVCO7Bq9t8S8"
_BAU_MIMIC_XP_MIN = 0.01      # 1%  — perda mínima de xp se o baú for um Mimic
_BAU_MIMIC_XP_MAX = 0.20      # 20% — perda máxima de xp se o baú for um Mimic

_XP_BOOSTER_DATA_FILE = os.path.join(_RPG_DATA_DIR, "xp_booster_data.json")

_xp_booster_ate: dict = {}    # user_id -> time.time() de quando o booster de xp em dobro expira


def _carregar_xp_booster_stats() -> None:
    """Carrega os boosters de xp em dobro (baú/boss/.darbosster) salvos em
    disco, se existirem. Roda antes do bot conectar — é isso que permite um
    booster ainda ativo sobreviver a um reinício do bot, em vez de sumir na
    hora. Boosters que já expiraram durante o tempo em que o bot ficou fora
    do ar são simplesmente ignorados (a checagem `time.time() < ate` já
    cuida disso sozinha)."""
    if not os.path.exists(_XP_BOOSTER_DATA_FILE):
        return
    try:
        with open(_XP_BOOSTER_DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        agora = time.time()
        for uid_str, ate in dados.get("ate", {}).items():
            if ate > agora:   # não vale a pena carregar o que já expirou
                _xp_booster_ate[int(uid_str)] = ate
    except (json.JSONDecodeError, OSError, ValueError):
        pass


async def _salvar_xp_booster_stats() -> None:
    """Salva os boosters de xp em dobro em disco de forma atômica (escreve em
    .tmp e substitui) — pra não perder o progresso quando o bot reiniciar."""
    dados = {
        "ate": {str(uid): ate for uid, ate in _xp_booster_ate.items()},
    }
    tmp_path = _XP_BOOSTER_DATA_FILE + ".tmp"

    def _escrever():
        os.makedirs(_RPG_DATA_DIR, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _XP_BOOSTER_DATA_FILE)

    try:
        loop = asyncio.get_event_loop()
        async with (_xp_stats_lock or asyncio.Lock()):
            await loop.run_in_executor(None, _escrever)
    except OSError:
        pass


def _conceder_xp_booster(user_id: int, minutos: float) -> None:
    """Concede (ou ESTENDE) o Booster de xp em dobro de alguém. Se a pessoa já
    tiver um ativo, soma `minutos` em cima do tempo que ainda resta, em vez de
    resetar pro valor cheio — assim dá pra empilhar vários boosters seguidos
    (baú, boss, .darbosster...) sem perder o que já tava rolando."""
    agora = time.time()
    inicio = max(agora, _xp_booster_ate.get(user_id, 0))
    _xp_booster_ate[user_id] = inicio + minutos * 60
    asyncio.create_task(_salvar_xp_booster_stats())


# Carrega os boosters de xp em dobro salvos em disco (baú/boss/.darbosster) —
# só é possível chamar aqui porque a função já foi definida acima.
_carregar_xp_booster_stats()


# ══════════════════════════════════════════════════════════════════════
# .darbosster — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Dá o Booster de xp (o mesmo prêmio raro do Baú: xp de call E de mensagem
# em dobro por _BAU_BOOSTER_MINUTOS minutos) direto pra alguém, sem precisar
# esperar o baú sortear. De propósito NÃO aparece em nenhum lugar do help.
# Uso (PV ou servidor): .darbosster <ID ou @membro>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="darbosster")
async def cmd_darbosster(ctx, alvo_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.darbosster <ID ou @membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    _conceder_xp_booster(alvo_id, _BAU_BOOSTER_MINUTOS)
    _empilhar_call_booster(alvo_id)

    confirmacao = await ctx.send(
        f"✅ Booster de xp (`x{_BAU_BOOSTER_MULTIPLICADOR}`, call e mensagem) empilhado pra "
        f"`{alvo_id}` por mais `{_BAU_BOOSTER_MINUTOS} min` — e o Booster de Call dela também "
        f"subiu +1 nível em cima do que já tinha."
    )
    await _apagar_mensagem_depois(confirmacao, 15)


# ══════════════════════════════════════════════════════════════════════
# .bostercall — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Igual o .darbosster, mas em massa: dá o Booster de xp (o mesmo prêmio raro
# do Baú, x2 em call E mensagem por _BAU_BOOSTER_MINUTOS minutos) + 1 nível
# de Booster de Call pra TODO MUNDO que estiver, agora, dentro do canal de
# voz indicado. De propósito NÃO aparece em nenhum lugar do help.
# Uso (PV ou servidor): .bostercall <ID do canal de voz>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="bostercall")
async def cmd_bostercall(ctx, canal_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if canal_id is None:
        aviso = await ctx.send("⚠️ Uso: `.bostercall <ID do canal de voz>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    canal_voz = guild.get_channel(canal_id) if guild else None
    if canal_voz is None:
        canal_voz = bot.get_channel(canal_id)

    if canal_voz is None or not isinstance(canal_voz, (discord.VoiceChannel, discord.StageChannel)):
        aviso = await ctx.send(f"❌ Não achei nenhum canal de voz com o ID `{canal_id}`.")
        await _apagar_mensagem_depois(aviso, 15)
        return

    membros = [m for m in canal_voz.members if not m.bot]
    if not membros:
        aviso = await ctx.send(f"⚠️ Não tem ninguém (sem contar bots) em **{canal_voz.name}** agora.")
        await _apagar_mensagem_depois(aviso, 15)
        return

    for membro in membros:
        _conceder_xp_booster(membro.id, _BAU_BOOSTER_MINUTOS)
        _empilhar_call_booster(membro.id)

    nomes = ", ".join(f"`{m.display_name}`" for m in membros)
    confirmacao = await ctx.send(
        f"✅ Booster de xp (`x{_BAU_BOOSTER_MULTIPLICADOR}`, call e mensagem) empilhado por mais "
        f"`{_BAU_BOOSTER_MINUTOS} min` pra todo mundo em **{canal_voz.name}** "
        f"(`{len(membros)}` pessoa{'s' if len(membros) != 1 else ''}) — e o Booster de Call de "
        f"cada um também subiu +1 nível em cima do que já tinha.\n{nomes}"
    )
    await _apagar_mensagem_depois(confirmacao, 30)


# ══════════════════════════════════════════════════════════════════════
# .vantagem — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Marca alguém pra GANHAR garantido a PRÓXIMA batalha (.desafio) que ela
# participar, seja como desafiante ou desafiada — pula o sorteio normal de
# vitória e o de roubo de XP: ela vence na hora e saqueia entre
# _VANTAGEM_ROUBO_MIN e _VANTAGEM_ROUBO_MAX (20% a 30%) garantido de XP da
# outra pessoa.
# A Vantagem fica "guardada" até a próxima batalha de verdade acontecer
# (não expira sozinha) e é consumida (removida) nesse momento.
# De propósito NÃO aparece em nenhum lugar do help/ajuda.
# Uso (PV ou servidor): .vantagem <ID ou @membro>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="vantagem")
async def cmd_vantagem(ctx, alvo_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.vantagem <ID ou @membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    _vantagem_ativa.add(alvo_id)

    confirmacao = await ctx.send(
        f"🍀✨ Vantagem concedida pra `{alvo_id}` — ela vai vencer garantido a próxima batalha que "
        f"participar, e vai saquear entre `{_VANTAGEM_ROUBO_MIN * 100:.0f}%` e "
        f"`{_VANTAGEM_ROUBO_MAX * 100:.0f}%` de XP garantido da outra pessoa."
    )
    await _apagar_mensagem_depois(confirmacao, 15)


# ══════════════════════════════════════════════════════════════════════
# .vantagemfossio — comando interno, só o Reality (CRIADOR_ID) pode usar.
# Parecida com .vantagem (vitória garantida), com 3 diferenças:
#   1. Só destrava numa batalha em que desafiante e desafiado estejam os
#      dois na MESMA call no momento do combate. Se a próxima batalha dela
#      rolar sem os dois em call juntos, a Vantagem fica pendente e não é
#      gasta — espera uma batalha em que a condição bata.
#   2. Rouba entre _VANTAGEM_FOSSIO_ROUBO_MIN e _MAX de XP (10% a 20%,
#      faixa própria, mais baixa que a do .vantagem normal).
#   3. Garante o desenterro de um 🦴 Fóssil nessa vitória também (pulando
#      o sorteio de _FOSSIL_CHANCE_DESBLOQUEIO), se ainda sobrar algum
#      Fóssil pra quem venceu destravar.
# Usa exatamente o mesmo texto de resultado/log de sempre — ninguém no
# chat consegue perceber que a batalha foi arranjada.
# De propósito NÃO aparece em nenhum lugar do help/ajuda.
# Uso (PV ou servidor): .vantagemfossio <ID ou @membro>
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="vantagemfossio")
async def cmd_vantagemfossio(ctx, alvo_id: int = None):
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        aviso = await ctx.send("⚠️ Uso: `.vantagemfossio <ID ou @membro>`")
        await _apagar_mensagem_depois(aviso, 15)
        return

    _vantagem_fossio_ativa.add(alvo_id)

    confirmacao = await ctx.send(
        f"🍀📞 Vantagem (call) concedida pra `{alvo_id}` — ela vai vencer garantido a próxima "
        f"batalha em que ela e a outra pessoa estiverem juntas numa call, vai saquear entre "
        f"`{_VANTAGEM_FOSSIO_ROUBO_MIN * 100:.0f}%` e `{_VANTAGEM_FOSSIO_ROUBO_MAX * 100:.0f}%` de "
        f"XP garantido da outra pessoa, e ainda desenterra um 🦴 Fóssil garantido (se sobrar algum "
        f"pra ela). Se não estiverem em call, essa batalha segue o sorteio normal e a Vantagem "
        f"continua guardada."
    )
    await _apagar_mensagem_depois(confirmacao, 15)


class BauView(discord.ui.View):
    """View do baú — só a PRIMEIRA pessoa que clicar leva o prêmio; quem
    clicar depois disso só recebe um aviso de que já foi levado.

    `forcar_secreto=True` é usado pelo .bausecreto: o visual e o texto são
    IDÊNTICOS ao baú normal (mesmo título, mesma descrição, mesmo gif) — só
    que quem clicar primeiro leva garantidamente uma criatura 🌌 Secreta
    ainda não desbloqueada, sem precisar do sorteio de _BAU_CHANCE_SECRETO.

    `forcar_mimic=True` é usado pelo .baumimic: visual e texto também
    IDÊNTICOS ao baú normal ANTES de abrir (é um Mimic disfarçado, ninguém
    pode desconfiar!) — mas quem clicar primeiro cai numa armadilha e PERDE
    entre _BAU_MIMIC_XP_MIN e _BAU_MIMIC_XP_MAX do XP dela, em vez de ganhar."""

    def __init__(self, forcar_secreto: bool = False, forcar_mimic: bool = False):
        super().__init__(timeout=None)
        self.aberto = False
        self.forcar_secreto = forcar_secreto
        self.forcar_mimic = forcar_mimic

    @discord.ui.button(label="🔓 Abrir o Baú", style=discord.ButtonStyle.success, custom_id="bau_abrir")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.aberto:
            await interaction.response.send_message(
                "👽 **Renan:** ...tarde demais. Alguém já levou.", ephemeral=True
            )
            return
        self.aberto = True

        membro = interaction.user
        dados = xp_stats[membro.id]
        dados.setdefault("criaturas", [])

        imagem_resultado = _BAU_GIF

        if self.forcar_mimic:
            # 👹 Era um Mimic disfarçado o tempo todo — em vez de prêmio,
            # rouba um % do XP atual da pessoa (entre _BAU_MIMIC_XP_MIN e
            # _BAU_MIMIC_XP_MAX). Não passa por nenhum outro sorteio.
            percentual = random.uniform(_BAU_MIMIC_XP_MIN, _BAU_MIMIC_XP_MAX)
            perda = max(1, round(dados["xp"] * percentual))
            dados["xp"] = max(0, dados["xp"] - perda)
            dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
            imagem_resultado = _BAU_MIMIC_GIF
            texto_premio = (
                f"👹💥 **ERA UM MIMIC!!** {membro.mention} abriu o baú e ele MOSTROU OS DENTES — "
                f"em vez de prêmio, levou uma mordida de **`-{perda}` XP** (`{percentual * 100:.1f}%`)! "
                "Que golpe de sorte ruim... 😨"
            )

            asyncio.create_task(_salvar_xp_stats())
            asyncio.create_task(_atualizar_ranking_xp())

            for item in self.children:
                item.disabled = True

            embed_resultado = discord.Embed(
                title="👹 Era um Mimic!!",
                description=texto_premio,
                color=0xaa2e2e,
                timestamp=discord.utils.utcnow(),
            )
            embed_resultado.set_image(url=imagem_resultado)
            embed_resultado.set_footer(text="👽 Renan — Baú do Tesouro")
            await interaction.response.edit_message(embed=embed_resultado, view=self)
            self.stop()
            return

        # 🌌 Prêmio mais raro de todos: uma criatura Secreta ainda não
        # desbloqueada. Se a pessoa já tiver as 6, cai pro sorteio normal
        # (booster/xp) em vez de travar sem ter mais nada pra dar — mesmo
        # no .bausecreto, que só GARANTE o secreto quando ainda sobra algum.
        _secretos_faltando = [
            c for c in _BATALHA_CRIATURAS
            if c["raridade"] == "secreto" and c["id"] not in dados["criaturas"]
        ]

        sai_secreto = bool(_secretos_faltando) and (self.forcar_secreto or random.random() < _BAU_CHANCE_SECRETO)

        if sai_secreto:
            criatura_secreta = random.choice(_secretos_faltando)
            dados["criaturas"].append(criatura_secreta["id"])
            info_raridade_secreta = _RARIDADES["secreto"]
            imagem_resultado = criatura_secreta["gif"]
            texto_premio = (
                f"🌌✨ **PRÊMIO RARÍSSIMO!!** {membro.mention} encontrou algo que quase ninguém acha... "
                f"{info_raridade_secreta['emoji']} **{criatura_secreta['nome']}** "
                f"(*{info_raridade_secreta['label']}*) foi desbloqueada e entrou pra sua coleção!! "
                f"Use `.criaturas` pra conferir. 🌌"
            )
        elif random.random() < _BAU_CHANCE_BOOSTER:
            # ── Prêmio raro: booster de 5 min que dobra xp de call e mensagem ──
            _conceder_xp_booster(membro.id, _BAU_BOOSTER_MINUTOS)
            texto_premio = (
                f"⚡✨ **PRÊMIO RARÍSSIMO!!** {membro.mention} ativou um **Booster de XP** — "
                f"pelos próximos `{_BAU_BOOSTER_MINUTOS} minutos`, todo xp de call e de mensagem vem "
                f"em **dobro**! ⚡✨"
            )
        else:
            percentual = random.uniform(_BAU_XP_MIN, _BAU_XP_MAX)
            nivel_antigo = dados["nivel"]
            ganho = max(5, round(dados["xp"] * percentual))
            ganho = min(ganho, _BAU_XP_TETO)
            dados["xp"] += ganho
            dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
            texto_premio = (
                f"💰 O baú sorteou **`{percentual * 100:.1f}%`**! {membro.mention} ganhou **`{ganho}` XP**!"
            )
            if dados["nivel"] > nivel_antigo and interaction.guild is not None:
                asyncio.create_task(_anunciar_level_up(interaction.guild, membro, dados["nivel"]))

        asyncio.create_task(_salvar_xp_stats())
        asyncio.create_task(_atualizar_ranking_xp())

        for item in self.children:
            item.disabled = True

        embed_resultado = discord.Embed(
            title="🪙 Baú Aberto!",
            description=texto_premio,
            color=0xf5c542,
            timestamp=discord.utils.utcnow(),
        )
        embed_resultado.set_image(url=imagem_resultado)
        embed_resultado.set_footer(text="👽 Renan — Baú do Tesouro")
        await interaction.response.edit_message(embed=embed_resultado, view=self)

        # 📜 Log do RPG — ganho orgânico do baú (secreto, booster ou XP).
        titulo_log = "🌌 Baú secreto — prêmio garantido" if self.forcar_secreto else "🪙 Baú aberto"
        asyncio.create_task(_log_rpg(interaction.guild, titulo_log, texto_premio))

        self.stop()


def _montar_embed_bau() -> discord.Embed:
    """Monta o embed de anúncio do baú — usado tanto pelo .bau normal quanto
    pelo .bausecreto, propositalmente IDÊNTICO nos dois, pra quem estiver no
    chat não conseguir diferenciar um do outro só de olhar."""
    embed = discord.Embed(
        title="🪙 Um Baú Apareceu!",
        description=(
            "👽 **Renan:** ...um baú misterioso. Quem clicar primeiro leva o prêmio. Corram — eu não "
            "espero por ninguém.\n\n"
            f"🎁 Prêmio: entre `{_BAU_XP_MIN * 100:.0f}%` e `{_BAU_XP_MAX * 100:.0f}%` de XP a mais — "
            f"mais raro, um **Booster de {_BAU_BOOSTER_MINUTOS} min** que dobra o xp de call e de "
            "mensagem — e, raríssimo mesmo, uma criatura de raridade 🌌 **Secreta** direto pra coleção!"
        ),
        color=0xf5c542,
    )
    embed.set_image(url=_BAU_GIF)
    embed.set_footer(text="👽 Renan — Baú do Tesouro")
    return embed


@bot.command(name="bau")
async def cmd_bau(ctx):
    """Joga um baú de recompensa no canal do chat geral — a primeira pessoa
    que clicar no botão leva o prêmio. Só o Reality pode usar. A própria
    mensagem do comando some logo em seguida. Uso: .bau"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BAU_CANAL_ID)
    if canal is None:
        return

    await canal.send(embed=_montar_embed_bau(), view=BauView())


@bot.command(name="bausecreto")
async def cmd_bausecreto(ctx):
    """Joga um baú IDÊNTICO ao .bau normal (mesmo visual, mesmo texto,
    ninguém no chat consegue diferenciar) — mas quem clicar primeiro leva
    GARANTIDAMENTE uma criatura 🌌 Secreta ainda não desbloqueada (a não
    ser que já tenha as 6, aí cai no sorteio normal do baú). Só o Reality
    pode usar. Uso: .bausecreto"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BAU_CANAL_ID)
    if canal is None:
        return

    await canal.send(embed=_montar_embed_bau(), view=BauView(forcar_secreto=True))


@bot.command(name="baumimic")
async def cmd_baumimic(ctx):
    """Joga um baú IDÊNTICO ao .bau normal (mesmo visual, mesmo texto,
    ninguém no chat consegue diferenciar) — mas é, na verdade, um Mimic
    disfarçado: quem clicar primeiro cai numa armadilha e PERDE entre
    `_BAU_MIMIC_XP_MIN` e `_BAU_MIMIC_XP_MAX` (até 20%) do XP dela, em vez
    de ganhar. Só o Reality pode usar. Uso: .baumimic"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BAU_CANAL_ID)
    if canal is None:
        return

    await canal.send(embed=_montar_embed_bau(), view=BauView(forcar_mimic=True))


# ══════════════════════════════════════════════════════════════════════
# BOSS — o Dragão do Caos
# Comando .boss (só o Reality/CRIADOR_ID pode ativar) invoca uma fera
# mítica gigantesca no canal _BOSS_CANAL_ID. O chat escolhe entre encarar
# sozinho (bem arriscado, só 5% de chance) ou chamar todo mundo pra lutar
# junto (mais gente = mais chance, mas ainda é um boss difícil de verdade).
# Cada pessoa convoca a criatura mais forte que já tem desbloqueada. Quem
# vence ganha entre 20% e 60% de XP a mais; quem perde não perde NADA —
# só o gostinho amargo da derrota. Todas as mensagens do evento somem
# sozinhas depois de 1 minuto.
# ══════════════════════════════════════════════════════════════════════

# ⚠️ Esse gif é um link temporário do CDN do Discord (parâmetros ?ex=...),
# que expira sozinho depois de um tempo (geralmente ~24h-48h). Se ele
# parar de aparecer no embed, pegue um link novo (clique direito na
# imagem no Discord > Copiar link) e troque aqui embaixo — ou, melhor
# ainda, suba o gif num host permanente (imgur, ibb.co etc.) pra nunca
# mais precisar trocar.
_BOSS_DRAGAO_CAOS_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1529955698690228294/gif-ezgif.com-optimize.gif?ex=6a63d1c7&is=6a628047&hm=7ce47d57d6827c7b60f48d9bb849950abdfe7893b460ef32a5a6755650ecc065"

_BOSS_CANAL_ID = 1501260061530390563  # canal de anúncios do RPG — só aparece aqui

_BOSS_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

_BOSS_CHANCE_SOLO = 0.05   # 5% — enfrentar sozinho é quase suicídio

# Batalha em grupo: começa numa base baixa, sobe um pouco por participante
# e um pouco mais conforme a raridade das criaturas convocadas — mas nunca
# passa de _BOSS_CHANCE_GRUPO_MAX, pra continuar sendo um boss difícil
# mesmo com o servidor inteiro batalhando junto.
_BOSS_CHANCE_GRUPO_BASE      = 0.12
_BOSS_CHANCE_GRUPO_MAX       = 0.70
_BOSS_BONUS_POR_PARTICIPANTE = 0.035
_BOSS_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.02, "epico": 0.035, "lendario": 0.06, "fosseis": 0.075, "secreto": 0.09, "mitico": 0.12,
}

_BOSS_XP_GANHO_MIN = 0.20   # 20% — mínimo de XP que quem vence pode ganhar
_BOSS_XP_GANHO_MAX = 0.60   # 60% — máximo de XP que quem vence pode ganhar
_BOSS_XP_GANHO_SEM_XP = (30, 80)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS_XP_GANHO_TETO = 3000   # teto máximo de XP por vitória — evita que rank alto dispare
                              # cada vez mais na frente do rank baixo. Ajuste esse número pra
                              # combinar com o nível mais alto real do seu servidor.

_boss_ativo_no_canal: set = set()   # channel_id -> impede 2 boss ao mesmo tempo no mesmo canal


def _boss_criatura_mais_forte(user_id: int) -> dict:
    """Retorna a criatura de MAIOR raridade que essa pessoa já desbloqueou —
    é ela que a pessoa convoca pra lutar contra o boss."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))
    for raridade in _ORDEM_RARIDADES:   # já vem do mais raro pro mais comum
        candidatas = [c for c in _BATALHA_CRIATURAS if c["raridade"] == raridade and c["id"] in desbloqueadas]
        if candidatas:
            return random.choice(candidatas)
    # segurança: nunca deveria cair aqui, todo mundo tem ao menos as Comuns
    return random.choice([c for c in _BATALHA_CRIATURAS if c["raridade"] == "comum"])


def _boss_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo: base + um bônus por pessoa +
    um bônus pela raridade de cada criatura convocada, sempre travado no
    teto de _BOSS_CHANCE_GRUPO_MAX pra continuar sendo um boss difícil."""
    chance = _BOSS_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS_BONUS_POR_PARTICIPANTE
    for membro, criatura in convocacoes:
        chance += _BOSS_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
        chance += _pet_bonus_chance_boss(membro.id)   # 🐾 bônus do Pet equipado (2% a 5%, + habilidade)
    chance += _pet_bonus_grupo_extra([m for m, _c in convocacoes])   # 🐾 habilidade de grupo (Renan)
    return min(chance, _BOSS_CHANCE_GRUPO_MAX)


def _boss_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer o boss: entre 20%
    e 60% do XP que ela já tem — travado num teto máximo (_BOSS_XP_GANHO_TETO)
    pra não deixar quem já é rank alto disparar cada vez mais na frente —
    ou uma recompensa fixa se ainda não tiver XP nenhum acumulado (pra
    ninguém sair de mãos vazias)."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS_XP_GANHO_MIN, _BOSS_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS_XP_GANHO_SEM_XP)
    return ganho, percentual


async def _boss_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor, atualiza nível e dispara o
    aviso de level up quando for o caso. Devolve uma lista de (membro,
    ganho, percentual) pra montar o texto de resultado."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        resultados.append((membro, ganho, percentual))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual in resultados:
        asyncio.create_task(_log_rpg(
            guild,
            "🐉 Recompensa — Dragão do Caos",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) "
            "por vencer o Dragão do Caos.",
        ))

    return resultados


async def _boss_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra o Dragão do Caos: só 5% de chance de
    vitória — e se perder, não perde XP nenhum, só o orgulho."""
    try:
        criatura = _boss_criatura_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]

        embed_convocacao = discord.Embed(
            title="🗡️ Um desafiante solitário se apresenta!",
            description=(
                f"👽 **Renan:** ...{membro.mention} decidiu enfrentar o Dragão do Caos sozinho. "
                f"Coragem ou loucura — eu ainda não sei dizer. {membro.display_name} convoca "
                f"{info_raridade['emoji']} **{criatura['nome']}**. Boa sorte, vai precisar de muita."
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        aviso = await canal.send("🐉💥 *O Dragão do Caos ruge e avança sobre o desafiante...* 💥🐉")
        await asyncio.sleep(2.5)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < (_BOSS_CHANCE_SOLO + _pet_bonus_chance_boss(membro.id))
        notas_pet = await _pet_pos_boss_grupo(canal.guild, [membro], venceu)   # 🐾 sobe o Pet, chance de upar criatura...

        if venceu:
            resultados = await _boss_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual = resultados[0]
            descricao = (
                f"🏆 **INACREDITÁVEL!!** {membro.mention} e {info_raridade['emoji']} **{criatura['nome']}** "
                f"derrubaram o **Dragão do Caos** sozinhos!! Só 5% de chance e AINDA ASSIM conseguiram!! 🐉💥\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`)\n\n"
                f"👽 **Renan:** ...impossível. E ainda assim, aconteceu. Eu me curvo. Isso é lenda viva."
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"💀 O **Dragão do Caos** foi forte demais — {info_raridade['emoji']} **{criatura['nome']}** caiu "
                f"em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...era esperado. Poucos sobrevivem à ousadia sozinhos. Não desanime — "
                "da próxima, chame a galera pra ir junto."
            )
            cor = 0x8b0000

        if notas_pet:
            descricao += f"\n\n{notas_pet}"

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — O Dragão do Caos")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


def _boss_cards_criaturas(convocacoes: list) -> list:
    """Monta um mini-embed pra CADA criatura convocada, com miniatura (igual
    ao que acontece no desafio solo) — assim dá pra ver o time inteiro de
    verdade, não só os nomes em texto. Discord aceita até 10 embeds por
    mensagem, então isso é enviado em lotes de 10 quando o grupo é grande."""
    cards = []
    for membro, criatura in convocacoes:
        info = _RARIDADES[criatura["raridade"]]
        card = discord.Embed(
            description=f"{info['emoji']} **{membro.display_name}** convoca **{criatura['nome']}** (*{info['label']}*)",
            color=info["cor"],
        )
        card.set_thumbnail(url=criatura["gif"])
        cards.append(card)
    return cards


async def _boss_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra o Dragão do Caos: cada participante
    convoca a criatura mais forte que já desbloqueou, e a chance de vitória
    cresce com o número (e a força) das criaturas convocadas."""
    try:
        convocacoes = [(p, _boss_criatura_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s entram em campo!",
            description="👽 **Renan:** ...olha só esse time. Vai ser intenso.",
            color=0xff4444,
        )
        cards = _boss_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        aviso = await canal.send("🐉💥 *O Dragão do Caos solta um rugido ensurdecedor e avança...* 💥🐉")
        await asyncio.sleep(2.5)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`)"
                for membro, ganho, percentual in resultados
            )
            descricao = (
                f"🏆 **VITÓRIA!!** O time de `{len(participantes)}` guerreiro(a)s derrubou o "
                f"**Dragão do Caos**!! (chance da batalha: `{chance * 100:.0f}%`) 🐉💥\n\n"
                f"{texto_ganhos}\n\n"
                f"👽 **Renan:** ...juntos, eu não teria chance contra vocês. Equipe dos sonhos."
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"💀 Mesmo com `{len(participantes)}` guerreiro(a)s juntos (`{chance * 100:.0f}%` de chance), "
                f"o **Dragão do Caos** foi forte demais dessa vez. {mencoes} não conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...nem sempre a união é suficiente. Eu respeito a tentativa. "
                "Tentem de novo da próxima vez — vocês foram corajosos."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — O Dragão do Caos")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class BossRecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS_TEMPO_RECRUTAMENTO segundos, juntando o time que vai enfrentar o
    boss em conjunto. Quando o tempo acaba, a batalha começa sozinha."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="⚔️ Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "👽 **Renan:** ...você já tá na lista.", ephemeral=True
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"⚔️ Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "👽 **Renan:** ...ninguém teve coragem de se juntar a tempo. "
                    "O Dragão do Caos ruge e desaparece."
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss_batalha_grupo(self.canal, participantes))


class BossEscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando o
    Dragão do Caos surge. A PRIMEIRA escolha feita (por qualquer pessoa)
    decide o caminho dessa aparição do boss."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} decidiu enfrentar o Dragão do Caos em "
                f"grupo. Quem tiver coragem, clique no botão abaixo. `{_BOSS_TEMPO_RECRUTAMENTO}s` "
                "pra se juntar ao time."
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS_DRAGAO_CAOS_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = BossRecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "🐉 Time contra o **Dragão do Caos** — clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🗡️ Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🗡️ DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} escolheu enfrentar o Dragão do Caos "
                "sozinho. Coragem, ou loucura. Só 5% de chance — vai precisar de muita sorte."
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS_DRAGAO_CAOS_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="🐉 O Dragão do Caos se foi...",
                description=(
                    "👽 **Renan:** ...ninguém teve coragem de decidir a tempo. O dragão volta a "
                    "dormir... por enquanto."
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss")
async def cmd_boss(ctx):
    """🐉 Invoca o Dragão do Caos no canal do chat geral — só o Reality
    (CRIADOR_ID) pode chamar. O chat escolhe entre encarar sozinho (5% de
    chance) ou juntar um time (mais gente = mais chance, mas ainda é um
    boss bem difícil). Uso: .boss"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "👽 **Renan:** ...já tem um Dragão do Caos ativo por lá. Espere esse terminar."
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="🐉 UM BOSS APARECEU!!",
        description=(
            "👽 **Renan:** ...algo antigo, furioso e imenso acaba de acordar. **O Dragão do Caos** "
            "chegou. Corram, ou fiquem e enfrentem — vocês decidem. Sozinhos, ou em equipe. Escolham "
            "com cuidado, ele é bem difícil.\n\n"
            f"⏳ Vocês têm `{_BOSS_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x8b0000,
    )
    embed.set_image(url=_BOSS_DRAGAO_CAOS_GIF)
    embed.set_footer(text="👽 Renan — Ameaça no Horizonte")

    view = BossEscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))



# ══════════════════════════════════════════════════════════════════════
# OVO — recompensa manual por vencer o Dragão do Caos
# Comando `.ovo <ID ou @membro>` (só o Reality/CRIADOR_ID pode usar) dá um
# 🥚 ovo pendente pra alguém. O ovo choca sozinho quando a pessoa acumular
# `_OVO_TEMPO_CHOCAR_SEGUNDOS` numa call — não precisa ser de uma vez só,
# o tempo soma mesmo se ela sair e voltar depois. Ao chocar, sai uma
# criatura aleatória (mesma lógica de recompensa das batalhas: prioriza
# uma que ela ainda não tem, ponderada por raridade, nunca Mítica) e o
# nascimento é anunciado no canal `_OVO_CANAL_ID`.
# ⚠️ `_ovos_pendentes` fica só em memória (igual o booster do baú) — um
# reinício do bot perde os ovos ainda chocando.
# ══════════════════════════════════════════════════════════════════════

_OVO_CANAL_ID = _XP_CANAL_1              # 1284257046740602901 — onde o nascimento é anunciado
_OVO_TEMPO_CHOCAR_SEGUNDOS = 5 * 60      # 5 minutos acumulados numa call pra chocar
_OVO_CHECAGEM_INTERVALO_SEGUNDOS = 20    # de quanto em quanto tempo confere quem já bateu a meta

# user_id -> {"tempo_acumulado": float, "entrou_em": float|None}
_ovos_pendentes: dict = {}


def _ovo_tempo_atual(user_id: int) -> float:
    """Tempo total (já acumulado + sessão em andamento, se houver) que essa
    pessoa já passou numa call desde que ganhou o ovo pendente."""
    ovo = _ovos_pendentes.get(user_id)
    if ovo is None:
        return 0.0
    total = ovo["tempo_acumulado"]
    if ovo["entrou_em"] is not None:
        total += time.time() - ovo["entrou_em"]
    return total


def _ovo_iniciar_contagem(user_id: int) -> None:
    """Chamada quando alguém com ovo pendente entra numa call — marca o
    início da sessão atual (se não tiver uma já rodando)."""
    ovo = _ovos_pendentes.get(user_id)
    if ovo is not None and ovo["entrou_em"] is None:
        ovo["entrou_em"] = time.time()


def _ovo_pausar_contagem(user_id: int) -> None:
    """Chamada quando alguém com ovo pendente sai da call — soma o tempo
    dessa sessão no acumulado e pausa a contagem até ela voltar."""
    ovo = _ovos_pendentes.get(user_id)
    if ovo is not None and ovo["entrou_em"] is not None:
        ovo["tempo_acumulado"] += time.time() - ovo["entrou_em"]
        ovo["entrou_em"] = None


async def _ovo_chocar(user_id: int) -> None:
    """Choca o ovo dessa pessoa: sorteia e concede uma criatura nova pra
    coleção dela, e anuncia no canal _OVO_CANAL_ID."""
    _ovos_pendentes.pop(user_id, None)

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    _nao_possuidas = [
        c for c in _BATALHA_CRIATURAS
        if c["id"] not in dados["criaturas"] and c["raridade"] not in ("mitico", "secreto", "fosseis", "bestas", "elemental")
    ]
    pool = _nao_possuidas or [c for c in _BATALHA_CRIATURAS if c["raridade"] not in ("mitico", "secreto", "fosseis", "bestas", "elemental")]
    pesos = [_RARIDADES[c["raridade"]]["peso"] for c in pool]
    criatura_nascida = random.choices(pool, weights=pesos, k=1)[0]
    if criatura_nascida["id"] not in dados["criaturas"]:
        dados["criaturas"].append(criatura_nascida["id"])
    asyncio.create_task(_salvar_xp_stats())

    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    canal = guild.get_channel(_OVO_CANAL_ID)
    if canal is None:
        return

    membro = guild.get_member(user_id)
    mencao = membro.mention if membro else f"<@{user_id}>"
    info_raridade = _RARIDADES[criatura_nascida["raridade"]]

    embed = discord.Embed(
        title="🥚✨ O Ovo Chocou!",
        description=(
            f"👽 **Renan:** ...{mencao}, seu ovo chocou. Depois de tanto tempo na call, olha só quem "
            f"nasceu: {info_raridade['emoji']} **{criatura_nascida['nome']}** "
            f"(*{info_raridade['label']}*). Eu aprovo.\n\n"
            "Use `.criaturas` pra conferir sua coleção. 📖"
        ),
        color=info_raridade["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=criatura_nascida["gif"])
    embed.set_footer(text="👽 Renan — Incubadora de Ovos")
    await canal.send(embed=embed)

    # 📜 Log do RPG — o ovo em si é presente manual do Reality (não logado),
    # mas o CHOCO é um evento automático (tempo acumulado em call) e conta
    # como ganho orgânico da pessoa.
    asyncio.create_task(_log_rpg(
        guild,
        "🥚 Ovo chocou",
        f"🥚 O ovo de **{membro.display_name if membro else user_id}** chocou, revelando "
        f"{info_raridade['emoji']} **{criatura_nascida['nome']}** (*{info_raridade['label']}*).",
    ))


@tasks.loop(seconds=_OVO_CHECAGEM_INTERVALO_SEGUNDOS)
async def loop_checar_ovos():
    """Roda a cada _OVO_CHECAGEM_INTERVALO_SEGUNDOS: confere se algum ovo
    pendente já bateu a meta de tempo em call — assim ele choca na hora,
    sem precisar esperar a pessoa sair da call pra descobrir."""
    for user_id in list(_ovos_pendentes.keys()):
        try:
            if _ovo_tempo_atual(user_id) >= _OVO_TEMPO_CHOCAR_SEGUNDOS:
                await _ovo_chocar(user_id)
        except Exception as e:
            print(f"[ovo] ERRO ao chocar ovo de {user_id}: {e!r}")


@bot.command(name="ovo")
async def cmd_ovo(ctx, alvo_id: int = None):
    """Dá um 🥚 ovo pendente pra alguém — recompensa por vencer o Dragão
    do Caos. O ovo choca sozinho quando a pessoa acumular
    `_OVO_TEMPO_CHOCAR_SEGUNDOS` numa call. Só o Reality pode usar.
    Uso: .ovo <ID ou @membro>"""
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        await ctx.send("⚠️ **Uso correto:** `.ovo <ID ou @membro>`")
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    membro = guild.get_member(alvo_id) if guild else None
    if membro is None and guild:
        try:
            membro = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            await ctx.send(f"❌ Membro com ID `{alvo_id}` não encontrado no servidor.")
            return

    _ovos_pendentes[alvo_id] = {"tempo_acumulado": 0.0, "entrou_em": None}
    # Se a pessoa já estiver numa call agora mesmo, a contagem já começa valendo.
    if membro is not None and membro.voice is not None and membro.voice.channel is not None:
        _ovo_iniciar_contagem(alvo_id)

    mencao = membro.mention if membro else f"`{alvo_id}`"
    await ctx.send(
        f"🐉💥 **Venceu do Dragão!** {mencao} agora tem direito a um **🥚 ovo aleatório**!! "
        f"Fique `{_OVO_TEMPO_CHOCAR_SEGUNDOS // 60} min` numa call pra ele chocar — "
        "o tempo soma mesmo se você sair e voltar depois."
    )


# ══════════════════════════════════════════════════════════════════════
# OVO DE DRAGÃO — igual ao .ovo normal, mas o ovo aqui é garantidamente
# um 🐉 Dragão (raridade mítica). Mesmíssima mecânica: `.ovodragao <ID ou
# @membro>` (só o Reality/CRIADOR_ID pode usar) dá o ovo pendente, a pessoa
# precisa acumular `_OVO_DRAGAO_TEMPO_CHOCAR_SEGUNDOS` numa call (o tempo
# soma mesmo saindo e voltando) e, ao chocar, nasce um dragão aleatório
# (prioriza um que ela ainda não tem). Tudo é anunciado no chat geral
# (`_OVO_DRAGAO_CANAL_ID`) — inclusive a entrega do ovo, com uma introdução
# mais épica que o ovo comum.
# ⚠️ `_ovos_dragao_pendentes` também fica só em memória — um reinício do
# bot perde os ovos de dragão ainda chocando.
# ══════════════════════════════════════════════════════════════════════

# Pool de dragões: todas as criaturas cujo id começa com "dragao_" — hoje
# são todas raridade mítica, mas o filtro é por id pra já valer
# automaticamente se algum dragão novo for adicionado no futuro.
_DRAGOES_DISPONIVEIS = [c for c in _BATALHA_CRIATURAS if c["id"].startswith("dragao_")]

_OVO_DRAGAO_CANAL_ID = _XP_CANAL_1                  # mesmo canal do chat geral — onde tudo é anunciado
_OVO_DRAGAO_TEMPO_CHOCAR_SEGUNDOS = 5 * 60          # 5 minutos acumulados numa call pra chocar
_OVO_DRAGAO_CHECAGEM_INTERVALO_SEGUNDOS = 20        # de quanto em quanto tempo confere quem já bateu a meta

# user_id -> {"tempo_acumulado": float, "entrou_em": float|None}
_ovos_dragao_pendentes: dict = {}


def _ovo_dragao_tempo_atual(user_id: int) -> float:
    """Tempo total (já acumulado + sessão em andamento, se houver) que essa
    pessoa já passou numa call desde que ganhou o ovo de dragão pendente."""
    ovo = _ovos_dragao_pendentes.get(user_id)
    if ovo is None:
        return 0.0
    total = ovo["tempo_acumulado"]
    if ovo["entrou_em"] is not None:
        total += time.time() - ovo["entrou_em"]
    return total


def _ovo_dragao_iniciar_contagem(user_id: int) -> None:
    """Chamada quando alguém com ovo de dragão pendente entra numa call —
    marca o início da sessão atual (se não tiver uma já rodando)."""
    ovo = _ovos_dragao_pendentes.get(user_id)
    if ovo is not None and ovo["entrou_em"] is None:
        ovo["entrou_em"] = time.time()


def _ovo_dragao_pausar_contagem(user_id: int) -> None:
    """Chamada quando alguém com ovo de dragão pendente sai da call — soma
    o tempo dessa sessão no acumulado e pausa a contagem até ela voltar."""
    ovo = _ovos_dragao_pendentes.get(user_id)
    if ovo is not None and ovo["entrou_em"] is not None:
        ovo["tempo_acumulado"] += time.time() - ovo["entrou_em"]
        ovo["entrou_em"] = None


async def _ovo_dragao_chocar(user_id: int) -> None:
    """Choca o ovo de dragão dessa pessoa: sorteia um 🐉 dragão (prioriza
    um que ela ainda não tem) pra coleção dela, e anuncia no chat geral."""
    _ovos_dragao_pendentes.pop(user_id, None)

    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])
    _dragoes_nao_possuidos = [
        c for c in _DRAGOES_DISPONIVEIS if c["id"] not in dados["criaturas"]
    ]
    pool = _dragoes_nao_possuidos or _DRAGOES_DISPONIVEIS
    pesos = [_RARIDADES[c["raridade"]]["peso"] for c in pool]
    dragao_nascido = random.choices(pool, weights=pesos, k=1)[0]
    if dragao_nascido["id"] not in dados["criaturas"]:
        dados["criaturas"].append(dragao_nascido["id"])
    asyncio.create_task(_salvar_xp_stats())

    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    canal = guild.get_channel(_OVO_DRAGAO_CANAL_ID)
    if canal is None:
        return

    membro = guild.get_member(user_id)
    mencao = membro.mention if membro else f"<@{user_id}>"
    info_raridade = _RARIDADES[dragao_nascido["raridade"]]

    embed = discord.Embed(
        title="🐉🥚 O Ovo do Dragão Chocou!",
        description=(
            f"👽 **Renan:** ...{mencao}, ele chocou. A espera valeu cada segundo — olha só o que "
            f"estava dormindo ali dentro: {info_raridade['emoji']} **{dragao_nascido['nome']}** "
            f"(*{info_raridade['label']}*). Um dragão reconhece outro guerreiro.\n\n"
            "Use `.criaturas` pra conferir sua coleção. 📖"
        ),
        color=info_raridade["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=dragao_nascido["gif"])
    embed.set_footer(text="👽 Renan — Incubadora de Dragões")
    await canal.send(embed=embed)


@tasks.loop(seconds=_OVO_DRAGAO_CHECAGEM_INTERVALO_SEGUNDOS)
async def loop_checar_ovos_dragao():
    """Roda a cada _OVO_DRAGAO_CHECAGEM_INTERVALO_SEGUNDOS: confere se
    algum ovo de dragão pendente já bateu a meta de tempo em call — assim
    ele choca na hora, sem precisar esperar a pessoa sair da call."""
    for user_id in list(_ovos_dragao_pendentes.keys()):
        try:
            if _ovo_dragao_tempo_atual(user_id) >= _OVO_DRAGAO_TEMPO_CHOCAR_SEGUNDOS:
                await _ovo_dragao_chocar(user_id)
        except Exception as e:
            print(f"[ovodragao] ERRO ao chocar ovo de dragão de {user_id}: {e!r}")


@bot.command(name="ovodragao", aliases=["ovodragão"])
async def cmd_ovodragao(ctx, alvo_id: int = None):
    """Dá um 🐉🥚 ovo de dragão pendente pra alguém. Igual ao .ovo normal,
    mas o que nasce é garantidamente um dragão. Anuncia a entrega no chat
    geral com uma introdução épica. Só o Reality pode usar.
    Uso: .ovodragao <ID ou @membro>"""
    if ctx.author.id != CRIADOR_ID:
        return

    if alvo_id is None and ctx.message.mentions:
        alvo_id = ctx.message.mentions[0].id
    if alvo_id is None:
        await ctx.send("⚠️ **Uso correto:** `.ovodragao <ID ou @membro>`")
        return

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    membro = guild.get_member(alvo_id) if guild else None
    if membro is None and guild:
        try:
            membro = await guild.fetch_member(alvo_id)
        except discord.NotFound:
            await ctx.send(f"❌ Membro com ID `{alvo_id}` não encontrado no servidor.")
            return

    _ovos_dragao_pendentes[alvo_id] = {"tempo_acumulado": 0.0, "entrou_em": None}
    # Se a pessoa já estiver numa call agora mesmo, a contagem já começa valendo.
    if membro is not None and membro.voice is not None and membro.voice.channel is not None:
        _ovo_dragao_iniciar_contagem(alvo_id)

    mencao = membro.mention if membro else f"<@{alvo_id}>"
    minutos = _OVO_DRAGAO_TEMPO_CHOCAR_SEGUNDOS // 60

    embed_intro = discord.Embed(
        title="🐉🥚 Um Ovo Lendário Surgiu...",
        description=(
            "**DIANTE DE INÚMERAS BATALHAS, UM OVO CAIU SOBRE SUAS MÃOS.**\n\n"
            f"👽 **Renan:** ...{mencao}. Eu senti o peso disso antes mesmo de acontecer. "
            "Algo ancestral dorme aí dentro — e não é uma criatura qualquer. Um ovo de dragão, pra "
            f"você. Fique `{minutos} min` numa call pra ele chocar — o tempo soma mesmo que você "
            "saia e volte depois. Boa sorte."
        ),
        color=_RARIDADES["mitico"]["cor"],
        timestamp=discord.utils.utcnow(),
    )
    embed_intro.set_footer(text="👽 Renan — Incubadora de Dragões")

    canal_geral = guild.get_channel(_OVO_DRAGAO_CANAL_ID) if guild else None
    if canal_geral is not None:
        await canal_geral.send(embed=embed_intro)

    # Se o comando foi usado fora do chat geral (ex.: no PV, como o .ovo normal),
    # manda uma confirmação simples pro Reality também.
    if canal_geral is None or ctx.channel.id != canal_geral.id:
        await ctx.send(f"✅ Ovo de dragão entregue pra {mencao} — anunciado no chat geral.")


# Comando .boss2 (só o Reality/CRIADOR_ID pode ativar) invoca o boss mais
# difícil já criado — Dourakhar, o Arauto da Morte. Mesma lógica do Dragão
# do Caos (encarar sozinho ou chamar o time todo), mas TUDO mais difícil:
# menos chance de vitória em qualquer cenário, mesmo com mais gente lutando
# junto. Em compensação, quem vencer ganha um pouco mais de XP que no boss 1
# E ainda leva um Booster de XP de 5 minutos (xp de call/mensagem em dobro).
# ══════════════════════════════════════════════════════════════════════

# ⚠️ Esses gifs são links temporários do CDN do Discord (parâmetros ?ex=...),
# que expiram sozinhos depois de um tempo (geralmente ~24h-48h). Se pararem
# de aparecer nos embeds, pegue links novos (clique direito na imagem no
# Discord > Copiar link) e troque aqui embaixo — ou, melhor ainda, subam
# os gifs num host permanente (imgur, ibb.co etc.) pra nunca mais precisar trocar.
_BOSS2_DOURAKHAR_INTRO_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530317596254142494/PixVerse_V6_Image_Text_720P_anime_se_mexendo_t1-ezgif.com-video-to-gif-converter.gif?ex=6a6522d2&is=6a63d152&hm=29fa9a7986126b02b81c108189d53806326f6ae1aabf5525267b297ac2fd63fd"
_BOSS2_DOURAKHAR_BATALHA_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530318926171476251/ezgif.com-video-to-gif-converter.gif?ex=6a65240f&is=6a63d28f&hm=d985c992e00eb66802330e6c13b6b3012c0998455cc6c18cbed1e3a66de9a21a"

_BOSS2_CANAL_ID = _BOSS_CANAL_ID   # mesmo canal do boss 1 — só aparece aqui

_BOSS2_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS2_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

_BOSS2_CHANCE_SOLO = 0.01   # 1% — nível mítico, enfrentar sozinho é praticamente suicídio (menos que o boss 1) [dificuldade aumentada]

# Batalha em grupo: base mais baixa e teto mais baixo que o boss 1 — mesma
# lógica (mais gente = mais chance, criaturas raras dão bônus extra), mas
# Dourakhar continua sendo bem mais difícil de derrubar mesmo com o
# servidor inteiro lutando junto. [valores reduzidos pra aumentar a dificuldade]
_BOSS2_CHANCE_GRUPO_BASE      = 0.05
_BOSS2_CHANCE_GRUPO_MAX       = 0.45
_BOSS2_BONUS_POR_PARTICIPANTE = 0.018
_BOSS2_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.01, "epico": 0.018, "lendario": 0.03, "secreto": 0.045, "mitico": 0.06,
}

_BOSS2_XP_GANHO_MIN = 0.25   # 25% — mínimo de XP que quem vence pode ganhar (um pouco melhor que o boss 1)
_BOSS2_XP_GANHO_MAX = 0.70   # 70% — máximo de XP que quem vence pode ganhar
_BOSS2_XP_GANHO_SEM_XP = (40, 100)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS2_XP_GANHO_TETO = 4000   # teto máximo de XP por vitória — um pouco mais alto que o boss 1
                                # (Dourakhar é mais raro/difícil), mas ainda travado pra não
                                # deixar o rank alto disparar cada vez mais na frente.


def _boss2_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo contra Dourakhar: base + um
    bônus por pessoa + um bônus pela raridade de cada criatura convocada,
    sempre travado no teto de _BOSS2_CHANCE_GRUPO_MAX — mais baixo que o
    do boss 1, porque Dourakhar é nível mítico."""
    chance = _BOSS2_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS2_BONUS_POR_PARTICIPANTE
    for _membro, criatura in convocacoes:
        chance += _BOSS2_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
    return min(chance, _BOSS2_CHANCE_GRUPO_MAX)


def _boss2_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer Dourakhar: entre
    25% e 70% do XP que ela já tem — um pouco melhor que o boss 1 — travado
    num teto máximo (_BOSS2_XP_GANHO_TETO) pra não deixar quem já é rank
    alto disparar cada vez mais na frente — ou uma recompensa fixa se
    ainda não tiver XP nenhum acumulado."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS2_XP_GANHO_MIN, _BOSS2_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS2_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS2_XP_GANHO_SEM_XP)
    return ganho, percentual


async def _boss2_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor, ativa o Booster de XP de 5
    minutos (xp de call/mensagem em dobro — mesmo mecanismo do Baú) pra
    cada um deles, atualiza nível e dispara o aviso de level up quando for
    o caso. Devolve uma lista de (membro, ganho, percentual) pra montar o
    texto de resultado."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss2_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        # 🎁 Bônus exclusivo de Dourakhar: Booster de XP de 5 minutos pra quem venceu
        _conceder_xp_booster(membro.id, _BAU_BOOSTER_MINUTOS)
        resultados.append((membro, ganho, percentual))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual in resultados:
        asyncio.create_task(_log_rpg(
            guild,
            "🐉 Recompensa — Dourakhar",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) + "
            f"⚡ Booster de XP de `{_BAU_BOOSTER_MINUTOS}min` por vencer Dourakhar.",
        ))

    return resultados


async def _boss2_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra Dourakhar: só 1% de chance de vitória —
    e se perder, não perde XP nenhum, só o orgulho."""
    try:
        criatura = _boss_criatura_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]

        embed_convocacao = discord.Embed(
            title="☠️ Um desafiante solitário ousa se apresentar!",
            description=(
                f"👽 **Renan:** ...{membro.mention} decidiu encarar Dourakhar sozinho. Eu nem sei se "
                f"isso é coragem ou uma despedida. {membro.display_name} convoca "
                f"{info_raridade['emoji']} **{criatura['nome']}**. É nível mítico — cuidado."
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "💀 **Dourakhar:** *\"Sozinho, mortal? Ousado... ou simplesmente tolo. "
                "Vamos ver qual dos dois é a verdade.\"*"
            ),
            color=0x2c0140,
        )
        embed_batalha.set_image(url=_BOSS2_DOURAKHAR_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < _BOSS2_CHANCE_SOLO

        if venceu:
            resultados = await _boss2_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual = resultados[0]
            descricao = (
                f"🏆 **LENDÁRIO DE VERDADE!!** {membro.mention} e {info_raridade['emoji']} **{criatura['nome']}** "
                f"derrubaram **DOURAKHAR, O ARAUTO DA MORTE**, SOZINHOS!! Só 1% de chance!! 💀⚔️\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`) + ⚡ **Booster de XP {_BAU_BOOSTER_MINUTOS}min**!\n\n"
                f"👽 **Renan:** ...impossível. A própria Morte hesitou. Eu não tenho palavras. "
                "Isso vai virar lenda no servidor inteiro."
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"💀 **Dourakhar:** *\"...como eu previa.\"* {info_raridade['emoji']} **{criatura['nome']}** caiu "
                f"em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...era esperado. Poucos ousam, menos ainda sobrevivem. Não desanime — "
                "contra esse aqui, é muito melhor ir em grupo."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — Dourakhar, o Arauto da Morte")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


async def _boss2_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra Dourakhar: cada participante
    convoca a criatura mais forte que já desbloqueou, e a chance de vitória
    cresce com o número (e a força) das criaturas convocadas — mas nível
    mítico continua sendo bem mais difícil que o boss 1."""
    try:
        convocacoes = [(p, _boss_criatura_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s ousam encarar a Morte!",
            description="👽 **Renan:** ...esse time tá indo contra o nível mítico. Boa sorte pra todos.",
            color=0x2c0140,
        )
        cards = _boss_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "💀 **Dourakhar:** *\"Um exército de formigas ainda é só um punhado de formigas... "
                "mas ao menos vocês me trazem entretenimento antes do fim. Venham.\"*"
            ),
            color=0x2c0140,
        )
        embed_batalha.set_image(url=_BOSS2_DOURAKHAR_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss2_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss2_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`) ⚡"
                for membro, ganho, percentual in resultados
            )
            descricao = (
                f"🏆 **VITÓRIA HISTÓRICA!!** O time de `{len(participantes)}` guerreiro(a)s derrubou "
                f"**DOURAKHAR, O ARAUTO DA MORTE**!! (chance da batalha: `{chance * 100:.0f}%`) 💀⚔️\n\n"
                f"{texto_ganhos}\n\n"
                f"⚡ Todos os vencedores também ganharam um **Booster de XP de {_BAU_BOOSTER_MINUTOS} minutos** "
                f"(xp de call e mensagem em dobro)!\n\n"
                f"👽 **Renan:** ...até a Morte tem seus limites, ao que parece. Eu me curvo a vocês. "
                "Vocês derrotaram o nível mítico — isso vai ficar na história do servidor."
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"💀 **Dourakhar:** *\"...como eu disse. Formigas.\"* Mesmo com `{len(participantes)}` "
                f"guerreiro(a)s juntos (`{chance * 100:.0f}%` de chance), o Arauto da Morte foi forte demais "
                f"dessa vez. {mencoes} não conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...nível mítico não perdoa fácil. Eu respeito a tentativa. "
                "Treinem e tentem de novo — vocês foram muito corajosos."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — Dourakhar, o Arauto da Morte")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class Boss2RecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS2_TEMPO_RECRUTAMENTO segundos, juntando o time que vai enfrentar
    Dourakhar em conjunto. Quando o tempo acaba, a batalha começa sozinha."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS2_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="⚔️ Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "👽 **Renan:** ...você já tá na lista.", ephemeral=True
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"⚔️ Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "👽 **Renan:** ...ninguém teve coragem de se juntar a tempo. "
                    "Dourakhar sorri e se dissolve... por enquanto."
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss2_batalha_grupo(self.canal, participantes))


class Boss2EscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando
    Dourakhar surge. A PRIMEIRA escolha feita (por qualquer pessoa) decide
    o caminho dessa aparição do boss."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS2_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} decidiu enfrentar Dourakhar em grupo. "
                f"Quem tiver coragem, clique no botão abaixo. `{_BOSS2_TEMPO_RECRUTAMENTO}s` pra se "
                "juntar ao time."
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS2_DOURAKHAR_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = Boss2RecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "💀 Time contra **Dourakhar, o Arauto da Morte** — clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🗡️ Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🗡️ DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} escolheu encarar Dourakhar sozinho. "
                "Isso não é coragem, isso é ousadia pura. Só 1% de chance — tem certeza?"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS2_DOURAKHAR_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss2_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="💀 Dourakhar se dissolve nas sombras...",
                description=(
                    "👽 **Renan:** ...ninguém teve coragem de decidir a tempo. O Arauto da Morte "
                    "se retira... por enquanto."
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss2")
async def cmd_boss2(ctx):
    """💀 Invoca Dourakhar, o Arauto da Morte — o boss de NÍVEL MÍTICO, mais
    difícil que o Dragão do Caos. Só o Reality (CRIADOR_ID) pode chamar.
    O chat escolhe entre encarar sozinho (1% de chance) ou juntar um time
    (mais gente = mais chance, mas ainda assim MUITO mais difícil que o
    boss 1). Quem vencer ganha um pouco mais de XP que no boss 1 e também
    leva um Booster de XP de 5 minutos. Uso: .boss2"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS2_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "👽 **Renan:** ...já tem um boss ativo por lá. Espere esse terminar."
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="☠️ NÍVEL MÍTICO — O ARAUTO DA MORTE DESPERTOU!!",
        description=(
            "👽 **Renan:** ...o próprio ar fica mais frio. Isso não é como o Dragão do Caos. "
            "Isso é diferente. Isso é o fim de tudo, caminhando.\n\n"
            "💀 **Dourakhar:** *\"Mortais... sintam o cheiro da própria finitude. Eu sou "
            "**Dourakhar**, o Arauto da Morte, e vim colher o que já me pertence.\"*\n\n"
            "Isso aqui é nível **mítico** — muito mais perigoso que o Dragão do Caos. Pensem bem "
            "antes de decidir: sozinho ou em grupo?\n\n"
            f"⏳ Vocês têm `{_BOSS2_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x2c0140,
    )
    embed.set_image(url=_BOSS2_DOURAKHAR_INTRO_GIF)
    embed.set_footer(text="👽 Renan — Nível Mítico: Dourakhar, o Arauto da Morte")

    view = Boss2EscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))


# ══════════════════════════════════════════════════════════════════════
# Comando .boss3 (só o Reality/CRIADOR_ID pode ativar) invoca Zephyrus, o
# Guardião do Véu Arcano — nível mítico, um pouco mais fraco que Dourakhar
# (boss2) mas ainda bem mais difícil que o Dragão do Caos (boss1). Mesma
# lógica de sempre (encarar sozinho ou chamar o time), mas Zephyrus entra
# em campo subestimando os desafiantes assim que a luta começa. Quem
# vencer ganha XP e leva um Booster de XP de apenas 2 minutos (mais curto
# que o de Dourakhar, condizente com o boss ser um pouco mais fraco).
# ══════════════════════════════════════════════════════════════════════

# ⚠️ Esses gifs são links temporários do CDN do Discord (parâmetros ?ex=...),
# que expiram sozinhos depois de um tempo (geralmente ~24h-48h). Se pararem
# de aparecer nos embeds, pegue links novos (clique direito na imagem no
# Discord > Copiar link) e troque aqui embaixo — ou, melhor ainda, subam
# os gifs num host permanente (imgur, ibb.co etc.) pra nunca mais precisar trocar.
_BOSS3_ZEPHYRUS_INTRO_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530395243793350656/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte1-ezgif.com-video-to-gif-converter.gif?ex=6a656b23&is=6a6419a3&hm=31a65b7384655f72f7bb1d274dddef20abd0f2a5476f4a650634418861d5cf2c&"
_BOSS3_ZEPHYRUS_BATALHA_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530395243336437971/PixVerse_V6_Image_Text_540P_faa_em_pixel_arte3-ezgif.com-video-to-gif-converter.gif?ex=6a656b23&is=6a6419a3&hm=7f3f861eccc45b6d93d8dbd437014814fd46196daec6cb535c34de7da748ad4b&"

_BOSS3_CANAL_ID = _BOSS_CANAL_ID   # mesmo canal dos outros bosses — só aparece aqui

_BOSS3_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS3_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

# Booster exclusivo do Zephyrus: mais curto que o dos outros bosses (2 min
# em vez dos 5 min do Baú/Dourakhar), condizente com ele ser um pouco mais fraco.
_BOSS3_BOOSTER_MINUTOS = 2

_BOSS3_CHANCE_SOLO = 0.03   # 3% — nível mítico, mas um pouco mais generoso que o 2% de Dourakhar

# Batalha em grupo: base e teto um pouco acima do boss2 (Dourakhar), mas
# ainda abaixo do boss1 (Dragão do Caos) — Zephyrus é "um pouco mais fraco"
# que Dourakhar, não fácil.
_BOSS3_CHANCE_GRUPO_BASE      = 0.095
_BOSS3_CHANCE_GRUPO_MAX       = 0.60
_BOSS3_BONUS_POR_PARTICIPANTE = 0.028
_BOSS3_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.009, "epico": 0.017, "lendario": 0.028, "secreto": 0.045, "mitico": 0.055,
}

_BOSS3_XP_GANHO_MIN = 0.22   # 22% — mínimo de XP que quem vence pode ganhar (entre o boss1 e o boss2)
_BOSS3_XP_GANHO_MAX = 0.65   # 65% — máximo de XP que quem vence pode ganhar
_BOSS3_XP_GANHO_SEM_XP = (35, 90)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS3_XP_GANHO_TETO = 3500   # teto máximo de XP por vitória — entre o teto do boss1 e do
                                # boss2 — evita que rank alto dispare cada vez mais na frente.


def _boss3_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo contra Zephyrus: base + um
    bônus por pessoa + um bônus pela raridade de cada criatura convocada,
    sempre travado no teto de _BOSS3_CHANCE_GRUPO_MAX — um pouco mais
    generoso que Dourakhar (boss2), mas ainda um boss de nível mítico."""
    chance = _BOSS3_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS3_BONUS_POR_PARTICIPANTE
    for _membro, criatura in convocacoes:
        chance += _BOSS3_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
    return min(chance, _BOSS3_CHANCE_GRUPO_MAX)


def _boss3_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer Zephyrus: entre
    22% e 65% do XP que ela já tem — travado num teto máximo
    (_BOSS3_XP_GANHO_TETO) pra não deixar quem já é rank alto disparar
    cada vez mais na frente — ou uma recompensa fixa se ainda não
    tiver XP nenhum acumulado."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS3_XP_GANHO_MIN, _BOSS3_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS3_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS3_XP_GANHO_SEM_XP)
    return ganho, percentual


async def _boss3_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor, ativa o Booster de XP de
    _BOSS3_BOOSTER_MINUTOS (mais curto que o dos outros bosses) pra cada
    um deles, atualiza nível e dispara o aviso de level up quando for o
    caso. Devolve uma lista de (membro, ganho, percentual)."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss3_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        # 🎁 Bônus exclusivo do Zephyrus: Booster de XP de apenas 2 minutos pra quem venceu
        _conceder_xp_booster(membro.id, _BOSS3_BOOSTER_MINUTOS)
        resultados.append((membro, ganho, percentual))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual in resultados:
        asyncio.create_task(_log_rpg(
            guild,
            "🌀 Recompensa — Zephyrus",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) + "
            f"⚡ Booster de XP de `{_BOSS3_BOOSTER_MINUTOS}min` por vencer Zephyrus.",
        ))

    return resultados


async def _boss3_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra Zephyrus: só 3% de chance de vitória —
    e se perder, não perde XP nenhum, só o orgulho."""
    try:
        criatura = _boss_criatura_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]

        embed_convocacao = discord.Embed(
            title="🌀 Um desafiante solitário ousa se apresentar!",
            description=(
                f"👽 **Renan:** ...{membro.mention} decidiu encarar Zephyrus sozinho. O véu se agita "
                f"como se estivesse rindo. {membro.display_name} convoca {info_raridade['emoji']} "
                f"**{criatura['nome']}**. É nível mítico — cuidado."
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "🌀 **Zephyrus:** *\"Sozinho? Eu já vi poeira com mais ambição que você, mortal. "
                "Mas tudo bem... vamos ver quanto tempo essa fagulha dura contra o véu.\"*"
            ),
            color=0x1b1033,
        )
        embed_batalha.set_image(url=_BOSS3_ZEPHYRUS_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < _BOSS3_CHANCE_SOLO

        if venceu:
            resultados = await _boss3_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual = resultados[0]
            descricao = (
                f"🏆 **O VÉU SE RASGOU!!** {membro.mention} e {info_raridade['emoji']} **{criatura['nome']}** "
                f"derrubaram **ZEPHYRUS, O GUARDIÃO DO VÉU ARCANO**, SOZINHOS!! Só 3% de chance!! 🌀⚔️\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`) + ⚡ **Booster de XP {_BOSS3_BOOSTER_MINUTOS}min**!\n\n"
                f"👽 **Renan:** ...ele subestimou. Foi o único erro que cometeu. Eu anoto isso. "
                "Ele duvidou e perdeu."
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"🌀 **Zephyrus:** *\"...como eu disse.\"* {info_raridade['emoji']} **{criatura['nome']}** caiu "
                f"em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...era esperado. O véu não se abre fácil. Não desanime — contra esse "
                "aqui também é bem melhor ir em grupo."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — Zephyrus, o Guardião do Véu Arcano")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


async def _boss3_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra Zephyrus: cada participante convoca
    a criatura mais forte que já desbloqueou, e a chance de vitória cresce
    com o número (e a força) das criaturas convocadas — um pouco mais fácil
    que Dourakhar (boss2), mas ainda nível mítico."""
    try:
        convocacoes = [(p, _boss_criatura_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s ousam encarar o véu!",
            description="👽 **Renan:** ...esse time tá indo contra o nível mítico. Boa sorte pra todos.",
            color=0x1b1033,
        )
        cards = _boss_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "🌀 **Zephyrus:** *\"Um bando de mortais batendo à porta do véu... adoráveis. "
                "Ingênuos, mas adoráveis. Vou tentar não bocejar enquanto isso acaba.\"*"
            ),
            color=0x1b1033,
        )
        embed_batalha.set_image(url=_BOSS3_ZEPHYRUS_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss3_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss3_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`) ⚡"
                for membro, ganho, percentual in resultados
            )
            descricao = (
                f"🏆 **O VÉU CEDEU!!** O time de `{len(participantes)}` guerreiro(a)s derrubou "
                f"**ZEPHYRUS, O GUARDIÃO DO VÉU ARCANO**!! (chance da batalha: `{chance * 100:.0f}%`) 🌀⚔️\n\n"
                f"{texto_ganhos}\n\n"
                f"⚡ Todos os vencedores também ganharam um **Booster de XP de {_BOSS3_BOOSTER_MINUTOS} minutos** "
                f"(xp de call e mensagem em dobro)!\n\n"
                f"👽 **Renan:** ...ele riu até o fim. Foi o erro dele. Eu respeito vocês. "
                "Ele achou que vocês eram fracos e se ferrou."
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"🌀 **Zephyrus:** *\"...eu avisei.\"* Mesmo com `{len(participantes)}` guerreiro(a)s "
                f"juntos (`{chance * 100:.0f}%` de chance), o Guardião do Véu Arcano foi forte demais "
                f"dessa vez. {mencoes} não conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...nível mítico não perdoa fácil, mesmo o mais fraco deles. "
                "Treinem e tentem de novo — vocês foram muito corajosos."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — Zephyrus, o Guardião do Véu Arcano")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class Boss3RecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS3_TEMPO_RECRUTAMENTO segundos, juntando o time que vai enfrentar
    Zephyrus em conjunto. Quando o tempo acaba, a batalha começa sozinha."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS3_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="⚔️ Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "👽 **Renan:** ...você já tá na lista.", ephemeral=True
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"⚔️ Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "👽 **Renan:** ...ninguém teve coragem de se juntar a tempo. "
                    "Zephyrus sorri e se dissolve de volta no véu... por enquanto."
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss3_batalha_grupo(self.canal, participantes))


class Boss3EscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando
    Zephyrus surge. A PRIMEIRA escolha feita (por qualquer pessoa) decide
    o caminho dessa aparição do boss."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS3_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} decidiu enfrentar Zephyrus em grupo. "
                f"Quem tiver coragem, clique no botão abaixo. `{_BOSS3_TEMPO_RECRUTAMENTO}s` pra se "
                "juntar ao time."
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS3_ZEPHYRUS_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = Boss3RecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "🌀 Time contra **Zephyrus, o Guardião do Véu Arcano** — clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🗡️ Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🗡️ DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} escolheu encarar Zephyrus sozinho. "
                "Isso não é coragem, isso é ousadia pura. Só 3% de chance — tem certeza?"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS3_ZEPHYRUS_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss3_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="🌀 Zephyrus se dissolve de volta no véu...",
                description=(
                    "👽 **Renan:** ...ninguém teve coragem de decidir a tempo. O Guardião "
                    "se retira... por enquanto."
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss3")
async def cmd_boss3(ctx):
    """🌀 Invoca Zephyrus, o Guardião do Véu Arcano — boss de NÍVEL MÍTICO,
    um pouco mais fraco que Dourakhar (boss2) mas ainda bem mais difícil
    que o Dragão do Caos (boss1). Só o Reality (CRIADOR_ID) pode chamar.
    O chat escolhe entre encarar sozinho (3% de chance) ou juntar um time
    (mais gente = mais chance). Quem vencer ganha XP e leva um Booster de
    XP de apenas 2 minutos. Uso: .boss3"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS3_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "👽 **Renan:** ...já tem um boss ativo por lá. Espere esse terminar."
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="🌀 NÍVEL MÍTICO — O GUARDIÃO DO VÉU ARCANO DESPERTOU!!",
        description=(
            "👽 **Renan:** ...o véu entre os mundos racha, e algo antigo espia através da fenda. "
            "Não é tão devastador quanto Dourakhar, mas ainda assim, nível mítico.\n\n"
            "🌀 **Zephyrus:** *\"Sinto o cheiro de mortais curiosos demais para o próprio bem. "
            "Eu sou **Zephyrus**, Guardião do Véu Arcano. Aproximem-se... se conseguirem.\"*\n\n"
            "Isso aqui também é nível **mítico** — mais fraco que Dourakhar, mas ainda muito mais "
            "perigoso que o Dragão do Caos. Sozinho ou em grupo?\n\n"
            f"⏳ Vocês têm `{_BOSS3_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x1b1033,
    )
    embed.set_image(url=_BOSS3_ZEPHYRUS_INTRO_GIF)
    embed.set_footer(text="👽 Renan — Nível Mítico: Zephyrus, o Guardião do Véu Arcano")

    view = Boss3EscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))


# ══════════════════════════════════════════════════════════════════════
# BOSS 4 — Cthulhu, o Ancião dos Abismos
# O boss mais forte e mais EXCLUSIVO de todos: ele simplesmente NÃO aceita
# nada abaixo de 🟡 Lendária. Quem desafiar (sozinho ou em grupo) sempre
# convoca a criatura Lendária de MAIOR Nível de Capacidade que já tiver —
# e quem não tiver nenhuma Lendária desbloqueada é recusado na hora, tanto
# no botão solo quanto no recrutamento em grupo.
#
# Dificuldade mítica, igual Dourakhar/Zephyrus — mas o bônus por
# participante é o MAIOR de todos os bosses: grupos grandes ganham chance
# desproporcionalmente mais rápido do que contra qualquer outro boss.
# ══════════════════════════════════════════════════════════════════════

_BOSS4_CTHULHU_INTRO_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530761640184905859/1785032338734.gif?ex=6a66c05f&is=6a656edf&hm=498a5804dc154079223effab883c04944c32d2451e5506d77a760c00f808017f"
_BOSS4_CTHULHU_BATALHA_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1530764368453701683/1785032847665.gif?ex=6a66c2e9&is=6a657169&hm=880fe48537da9be053f931f2f76c870f154f3f21d4a02685976ceceec849c994"

_BOSS4_CANAL_ID = _BOSS_CANAL_ID   # mesmo canal dos outros bosses — só aparece aqui

_BOSS4_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS4_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

# Booster exclusivo do Cthulhu: o mais longo de todos os bosses (5 min,
# igual o do Baú), condizente com ele ser o boss mais forte e difícil.
_BOSS4_BOOSTER_MINUTOS = 5

_BOSS4_CHANCE_SOLO = 0.01   # 1% — nível mítico, tão difícil sozinho quanto Dourakhar

# Batalha em grupo: a base mais baixa de todos os bosses, mas o bônus por
# participante é o MAIOR — grupos grandes recuperam terreno muito mais
# rápido do que contra qualquer outro boss.
_BOSS4_CHANCE_GRUPO_BASE      = 0.04
_BOSS4_CHANCE_GRUPO_MAX       = 0.65
_BOSS4_BONUS_POR_PARTICIPANTE = 0.045
_BOSS4_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.0, "epico": 0.0, "lendario": 0.035, "secreto": 0.05, "mitico": 0.06,
}

_BOSS4_XP_GANHO_MIN = 0.25    # 25% — mínimo de XP que quem vence pode ganhar (o melhor de todos os bosses)
_BOSS4_XP_GANHO_MAX = 0.75    # 75% — máximo de XP que quem vence pode ganhar
_BOSS4_XP_GANHO_SEM_XP = (45, 110)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS4_XP_GANHO_TETO = 4500    # teto máximo de XP por vitória — o maior de todos os bosses
                                 # (Cthulhu é o mais raro), mas ainda travado pra não deixar
                                 # o rank alto disparar cada vez mais na frente.


def _boss4_criatura_lendaria_mais_forte(user_id: int):
    """Cthulhu só aceita quem convocar uma criatura 🟡 Lendária — e sempre
    puxa a de MAIOR Nível de Capacidade que a pessoa tiver, entre as
    Lendárias que ela já desbloqueou. Devolve None se a pessoa não tiver
    nenhuma Lendária (nesse caso, ela é recusada pelo boss)."""
    desbloqueadas = set(_garantir_criaturas_iniciais(user_id))
    lendarias = [c for c in _BATALHA_CRIATURAS if c["raridade"] == "lendario" and c["id"] in desbloqueadas]
    if not lendarias:
        return None
    return max(lendarias, key=lambda c: _nivel_criatura(user_id, c["id"]))


def _boss4_cards_criaturas(convocacoes: list) -> list:
    """Igual _boss_cards_criaturas, mas também mostra o Nível de Capacidade
    de cada Lendária convocada — já que é sempre a mais forte E de maior
    nível que cada um tem."""
    cards = []
    for membro, criatura in convocacoes:
        info = _RARIDADES[criatura["raridade"]]
        nivel_atual = _nivel_criatura(membro.id, criatura["id"])
        nivel_teto = _nivel_criatura_max(criatura["id"])
        card = discord.Embed(
            description=(
                f"{info['emoji']} **{membro.display_name}** convoca **{criatura['nome']}** "
                f"(*{info['label']}*, Nível `{nivel_atual}/{nivel_teto}`)"
            ),
            color=info["cor"],
        )
        card.set_thumbnail(url=criatura["gif"])
        cards.append(card)
    return cards


def _boss4_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo contra Cthulhu: base baixa +
    um bônus por pessoa (o maior de todos os bosses) + um bônus pela
    raridade de cada Lendária convocada, travado no teto de
    _BOSS4_CHANCE_GRUPO_MAX."""
    chance = _BOSS4_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS4_BONUS_POR_PARTICIPANTE
    for _membro, criatura in convocacoes:
        chance += _BOSS4_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
    return min(chance, _BOSS4_CHANCE_GRUPO_MAX)


def _boss4_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer Cthulhu: entre 25%
    e 75% do XP que ela já tem — a melhor faixa de recompensa entre todos
    os bosses — travado num teto máximo (_BOSS4_XP_GANHO_TETO) pra não
    deixar quem já é rank alto disparar cada vez mais na frente — ou uma
    recompensa fixa se ainda não tiver XP acumulado."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS4_XP_GANHO_MIN, _BOSS4_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS4_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS4_XP_GANHO_SEM_XP)
    return ganho, percentual


async def _boss4_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor, ativa o Booster de XP de
    _BOSS4_BOOSTER_MINUTOS (5 min — o maior de todos os bosses) pra cada
    um deles, atualiza nível e dispara o aviso de level up quando for o
    caso. Devolve uma lista de (membro, ganho, percentual)."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss4_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        # 🎁 Bônus do Cthulhu: Booster de XP de 5 minutos pra quem venceu
        _conceder_xp_booster(membro.id, _BOSS4_BOOSTER_MINUTOS)
        resultados.append((membro, ganho, percentual))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual in resultados:
        asyncio.create_task(_log_rpg(
            guild,
            "🐙 Recompensa — Cthulhu",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) + "
            f"⚡ Booster de XP de `{_BOSS4_BOOSTER_MINUTOS}min` por vencer Cthulhu.",
        ))

    return resultados


async def _boss4_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra Cthulhu: só 1% de chance de vitória —
    e se perder, não perde XP nenhum, só o orgulho. Só é chamada depois
    que o botão já garantiu que `membro` tem uma Lendária."""
    try:
        criatura = _boss4_criatura_lendaria_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]
        nivel_atual = _nivel_criatura(membro.id, criatura["id"])
        nivel_teto = _nivel_criatura_max(criatura["id"])

        embed_convocacao = discord.Embed(
            title="🐙 Um desafiante solitário ousa se apresentar!",
            description=(
                f"👽 **Renan:** ...{membro.mention} decidiu encarar Cthulhu sozinho. As profundezas "
                f"nem se incomodam em despertar de verdade. {membro.display_name} convoca "
                f"{info_raridade['emoji']} **{criatura['nome']}** (Nível `{nivel_atual}/{nivel_teto}`). "
                "É nível mítico — cuidado."
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "🐙 **Cthulhu:** *\"Uma única fagulha... contra o abismo inteiro? Eu nem preciso "
                "acordar direito pra isso.\"*"
            ),
            color=0x0d2b2e,
        )
        embed_batalha.set_image(url=_BOSS4_CTHULHU_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < _BOSS4_CHANCE_SOLO

        if venceu:
            resultados = await _boss4_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual = resultados[0]
            descricao = (
                f"🏆 **O IMPOSSÍVEL ACONTECEU!!** {membro.mention} e {info_raridade['emoji']} "
                f"**{criatura['nome']}** derrubaram **CTHULHU, O ANCIÃO DOS ABISMOS**, SOZINHOS!! "
                f"Só `{_BOSS4_CHANCE_SOLO * 100:.0f}%` de chance!! 🐙⚔️\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`) + ⚡ **Booster de XP "
                f"{_BOSS4_BOOSTER_MINUTOS}min**!\n\n"
                f"👽 **Renan:** ...ele nem viu chegando. Nem os Anciões estão a salvo do próprio "
                "orgulho. Isso foi lendário de verdade — ninguém vai acreditar nisso."
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"🐙 **Cthulhu:** *\"...como eu disse.\"* {info_raridade['emoji']} **{criatura['nome']}** "
                f"caiu em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...era esperado. Nem uma Lendária sozinha abala os abismos. Contra "
                "ele, é muito melhor ir em grupo — quanto mais gente, mais chance."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — Cthulhu, o Ancião dos Abismos")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


async def _boss4_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra Cthulhu: cada participante convoca
    a Lendária mais forte (maior nível) que já desbloqueou, e a chance de
    vitória cresce MAIS RÁPIDO com o número de participantes do que contra
    qualquer outro boss — mas a base é a mais baixa de todos."""
    try:
        convocacoes = [(p, _boss4_criatura_lendaria_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s ousam despertar o abismo!",
            description=(
                "👽 **Renan:** ...esse time tá indo contra o boss mais forte de todos. "
                "Só Lendárias entraram nessa — boa sorte."
            ),
            color=0x0d2b2e,
        )
        cards = _boss4_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "🐙 **Cthulhu:** *\"Um exército de mortais, cada um com sua melhor Lendária... "
                "finalmente algo quase digno da minha atenção. Quase.\"*"
            ),
            color=0x0d2b2e,
        )
        embed_batalha.set_image(url=_BOSS4_CTHULHU_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss4_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss4_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`) ⚡"
                for membro, ganho, percentual in resultados
            )
            descricao = (
                f"🏆 **O ABISMO SE CALOU!!** O time de `{len(participantes)}` guerreiro(a)s derrubou "
                f"**CTHULHU, O ANCIÃO DOS ABISMOS**!! (chance da batalha: `{chance * 100:.0f}%`) 🐙⚔️\n\n"
                f"{texto_ganhos}\n\n"
                f"⚡ Todos os vencedores também ganharam um **Booster de XP de {_BOSS4_BOOSTER_MINUTOS} "
                f"minutos** (xp de call e mensagem em dobro)!\n\n"
                f"👽 **Renan:** ...nem os Anciões dormem tranquilos pra sempre. Eu vou lembrar disso. "
                "Vocês derrubaram o boss mais forte de todos — isso é histórico."
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"🐙 **Cthulhu:** *\"...voltem quando forem mais.\"* Mesmo com `{len(participantes)}` "
                f"guerreiro(a)s Lendários juntos (`{chance * 100:.0f}%` de chance), o Ancião dos "
                f"Abismos foi forte demais dessa vez. {mencoes} não conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...ele é o mais forte de todos por um motivo. Quanto mais gente, "
                "muito mais chance — chamem reforços e tentem de novo."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — Cthulhu, o Ancião dos Abismos")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class Boss4RecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS4_TEMPO_RECRUTAMENTO segundos. Diferente dos outros bosses, quem
    clicar SEM ter uma criatura 🟡 Lendária desbloqueada é recusado na hora
    (Cthulhu não aceita menos que isso) — não entra pra lista."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS4_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="🐙 Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "👽 **Renan:** ...você já tá na lista.", ephemeral=True
            )
            return
        if _boss4_criatura_lendaria_mais_forte(interaction.user.id) is None:
            await interaction.response.send_message(
                "👽 **Renan:** ...Cthulhu nem notaria suas criaturas atuais. Só quem tiver uma "
                "criatura 🟡 Lendária desbloqueada pode entrar nessa.",
                ephemeral=True,
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"🐙 Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "👽 **Renan:** ...ninguém digno se juntou a tempo. Cthulhu volta a dormir nas "
                    "profundezas... por enquanto."
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss4_batalha_grupo(self.canal, participantes))


class Boss4EscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando
    Cthulhu desperta. A PRIMEIRA escolha feita (por qualquer pessoa) decide
    o caminho dessa aparição do boss. O botão solo recusa na hora quem não
    tiver uma Lendária desbloqueada."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS4_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} decidiu enfrentar Cthulhu em grupo. "
                "Só criaturas 🟡 Lendárias vão ser aceitas. Quem tiver uma e coragem, clique no botão "
                f"abaixo. `{_BOSS4_TEMPO_RECRUTAMENTO}s` pra se juntar ao time."
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS4_CTHULHU_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = Boss4RecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "🐙 Time contra **Cthulhu, o Ancião dos Abismos** — só Lendárias, clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🐙 Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        if _boss4_criatura_lendaria_mais_forte(interaction.user.id) is None:
            await interaction.response.send_message(
                "👽 **Renan:** ...suas criaturas atuais nem seriam notadas por Cthulhu. Só quem "
                "tiver uma criatura 🟡 Lendária desbloqueada pode desafiá-lo.",
                ephemeral=True,
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🐙 DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} escolheu encarar Cthulhu sozinho. Isso "
                "não é coragem, isso é loucura pura. Só "
                f"`{_BOSS4_CHANCE_SOLO * 100:.0f}%` de chance — é o boss mais forte de todos, tem certeza?"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS4_CTHULHU_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss4_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="🐙 Cthulhu volta a dormir nas profundezas...",
                description=(
                    "👽 **Renan:** ...ninguém teve coragem de decidir a tempo. O Ancião se recolhe... "
                    "por enquanto."
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss4")
async def cmd_boss4(ctx):
    """🐙 Invoca Cthulhu, o Ancião dos Abismos — o boss mais forte e mais
    EXCLUSIVO de todos: só aceita quem convocar uma criatura 🟡 Lendária (e
    sempre puxa a Lendária de maior Nível de Capacidade que a pessoa
    tiver) — quem não tiver nenhuma é recusado na hora. Dificuldade
    mítica, com o bônus por participante MAIS FORTE de todos os bosses:
    quanto mais gente entrar, mais rápido a chance sobe. Só o Reality
    (CRIADOR_ID) pode chamar. Quem vencer ganha XP e um Booster de XP de
    5 minutos — o maior de todos os bosses. Uso: .boss4"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS4_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "👽 **Renan:** ...já tem um boss ativo por lá. Espere esse terminar."
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="🐙 NÍVEL MÍTICO — CTHULHU DESPERTOU NOS ABISMOS!!",
        description=(
            "👽 **Renan:** ...o oceano racha e algo imensurável abre os olhos pela primeira vez em "
            "eras. Ele nem se dá ao trabalho de se levantar por completo.\n\n"
            "🐙 **Cthulhu:** *\"Mortais... e suas criaturinhas fracas. Não me insultem com o que "
            "vocês chamam de 'comum'. Só as suas Lendárias são dignas de olhar pra mim — as demais, "
            "eu nem enxergo.\"*\n\n"
            "Ele só aceita criatura 🟡 Lendária. E ainda por cima é nível **mítico** — o mais forte "
            "de todos os bosses. Sozinho ou em grupo? Quanto mais gente, muito mais chance.\n\n"
            f"⏳ Vocês têm `{_BOSS4_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x0d2b2e,
    )
    embed.set_image(url=_BOSS4_CTHULHU_INTRO_GIF)
    embed.set_footer(text="👽 Renan — Nível Mítico: Cthulhu, o Ancião dos Abismos")

    view = Boss4EscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))


# ══════════════════════════════════════════════════════════════════════
# BOSS 5 — Kaelith, a Ceifadora dos Reis
# A própria Morte em pessoa — tão temida quanto Dourakhar (boss2), mas
# ligeiramente mais fraca que ele: Dourakhar continua sendo o boss mais
# forte de todos. Mesma lógica de sempre (encarar sozinho ou chamar o
# time todo), nível mítico.
#
# Kaelith não dá tanto XP quanto os outros bosses — é a recompensa de XP
# mais modesta de todas — mas compensa com dois prêmios extras pra quem
# vence: um Booster de XP de 10 minutos (o mais longo de todos os bosses)
# e uma CHANCE de vir junto um 🥚 ovo aleatório, sorteado só entre
# criaturas 🟣 Épicas e 🟡 Lendárias. Se a criatura que sair já estiver na
# coleção da pessoa, em vez de não fazer nada ela sobe 1 Nível de
# Capacidade (mesma lógica de .uparcriatura), travado no teto máximo.
# ══════════════════════════════════════════════════════════════════════

# ⚠️ Esses gifs são links temporários do CDN do Discord (parâmetros ?ex=...),
# que expiram sozinhos depois de um tempo (geralmente ~24h-48h). Se pararem
# de aparecer nos embeds, pegue links novos (clique direito na imagem no
# Discord > Copiar link) e troque aqui embaixo — ou, melhor ainda, subam
# os gifs num host permanente (imgur, ibb.co etc.) pra nunca mais precisar trocar.
_BOSS5_KAELITH_INTRO_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1531429255978942464/1785191174797.gif?ex=6a692e23&is=6a67dca3&hm=a82d8cbf2e94d0f9fda33c4a8ee2aa985bcbbb8763d0118cd08c8b333910bb2a&"
_BOSS5_KAELITH_BATALHA_GIF = "https://cdn.discordapp.com/attachments/926913851172204577/1531429255328698379/1785191374952.gif?ex=6a692e23&is=6a67dca3&hm=6229f85c09a13d8deb3ae310b676f4191af497c9a7cc2d27ccc709475f1ac7a4&"

_BOSS5_CANAL_ID = _BOSS_CANAL_ID   # mesmo canal dos outros bosses — só aparece aqui

_BOSS5_TEMPO_ESCOLHA      = 60   # segundos pra decidir "todos juntos" ou "sozinho"
_BOSS5_TEMPO_RECRUTAMENTO = 10   # segundos pra galera clicar "quero participar" depois de "todos juntos"

# Booster exclusivo de Kaelith: o MAIS LONGO de todos os bosses (10 min),
# uma forma de compensar o XP mais baixo que ela dá.
_BOSS5_BOOSTER_MINUTOS = 10

# Nível mítico, ligeiramente mais fácil que Dourakhar (boss2) em todos os
# números — mas ainda o segundo boss mais difícil do servidor.
_BOSS5_CHANCE_SOLO = 0.012   # 1.2% — um pouco mais generoso que o 1% de Dourakhar

_BOSS5_CHANCE_GRUPO_BASE      = 0.055
_BOSS5_CHANCE_GRUPO_MAX       = 0.48
_BOSS5_BONUS_POR_PARTICIPANTE = 0.019
_BOSS5_BONUS_RARIDADE_CRIATURA = {
    "comum": 0.0, "raro": 0.01, "epico": 0.018, "lendario": 0.03, "secreto": 0.045, "mitico": 0.06,
}

# XP mais modesto que qualquer outro boss — Kaelith compensa com o Booster
# de 10 min e a chance de ovo Épico/Lendário, não com XP bruto.
_BOSS5_XP_GANHO_MIN = 0.15    # 15% — mínimo de XP que quem vence pode ganhar (o mais baixo de todos os bosses)
_BOSS5_XP_GANHO_MAX = 0.45    # 45% — máximo de XP que quem vence pode ganhar
_BOSS5_XP_GANHO_SEM_XP = (20, 55)   # recompensa fixa pra quem ainda não tem XP acumulado
_BOSS5_XP_GANHO_TETO = 2000    # teto máximo de XP por vitória — o menor de todos os bosses

# 🥚 Chance de vir um ovo junto com a vitória, sorteado só entre criaturas
# 🟣 Épicas e 🟡 Lendárias (pool restrito — nunca sai Comum/Rara/Mítica/etc
# desse ovo). Ajuste esse número se quiser o ovo mais raro ou mais comum.
_BOSS5_CHANCE_OVO = 0.35   # 35% de chance por vencedor
_BOSS5_OVO_RARIDADES = ("epico", "lendario")


def _boss5_chance_grupo(convocacoes: list) -> float:
    """Calcula a chance de vitória do grupo contra Kaelith: base + um
    bônus por pessoa + um bônus pela raridade de cada criatura convocada,
    sempre travado no teto de _BOSS5_CHANCE_GRUPO_MAX — ligeiramente mais
    generoso que Dourakhar (boss2), mas ainda nível mítico."""
    chance = _BOSS5_CHANCE_GRUPO_BASE + len(convocacoes) * _BOSS5_BONUS_POR_PARTICIPANTE
    for _membro, criatura in convocacoes:
        chance += _BOSS5_BONUS_RARIDADE_CRIATURA.get(criatura["raridade"], 0.0)
    return min(chance, _BOSS5_CHANCE_GRUPO_MAX)


def _boss5_calcular_ganho_xp(user_id: int) -> tuple:
    """Sorteia quanto de XP essa pessoa ganha por vencer Kaelith: entre 15%
    e 45% do XP que ela já tem — a faixa mais baixa entre todos os bosses —
    travado num teto máximo (_BOSS5_XP_GANHO_TETO) pra não deixar quem já é
    rank alto disparar cada vez mais na frente — ou uma recompensa fixa se
    ainda não tiver XP nenhum acumulado."""
    dados = xp_stats[user_id]
    xp_atual = dados.get("xp", 0)
    if xp_atual > 0:
        percentual = random.uniform(_BOSS5_XP_GANHO_MIN, _BOSS5_XP_GANHO_MAX)
        ganho = max(1, round(xp_atual * percentual))
        ganho = min(ganho, _BOSS5_XP_GANHO_TETO)
    else:
        percentual = 0.0
        ganho = random.randint(*_BOSS5_XP_GANHO_SEM_XP)
    return ganho, percentual


def _boss5_sortear_criatura_ovo() -> dict:
    """Sorteia uma criatura aleatória só entre 🟣 Épicas e 🟡 Lendárias
    (ponderada pelo peso normal de raridade) — é essa a criatura que pode
    vir no ovo de Kaelith."""
    pool = [c for c in _BATALHA_CRIATURAS if c["raridade"] in _BOSS5_OVO_RARIDADES]
    pesos = [_RARIDADES[c["raridade"]]["peso"] for c in pool]
    return random.choices(pool, weights=pesos, k=1)[0]


def _boss5_conceder_ovo(user_id: int) -> dict:
    """Sorteia o ovo de Kaelith pra essa pessoa (só Épica ou Lendária). Se
    ela ainda não tiver essa criatura, ela é adicionada normalmente à
    coleção. Se ela JÁ tiver (repetida), em vez de não fazer nada, a
    criatura sobe 1 Nível de Capacidade — empurrando os usos pro limiar do
    próximo nível, igual `.uparcriatura` — travado no teto máximo (se já
    estiver no máximo, o ovo simplesmente não muda nada). Devolve um dict
    com `criatura`, `era_nova`, `nivel_novo` (ou None se era nova) e
    `upou` (True se realmente subiu de nível agora)."""
    criatura = _boss5_sortear_criatura_ovo()
    dados = xp_stats[user_id]
    dados.setdefault("criaturas", [])

    if criatura["id"] not in dados["criaturas"]:
        dados["criaturas"].append(criatura["id"])
        return {"criatura": criatura, "era_nova": True, "nivel_novo": None, "upou": False}

    teto = _nivel_criatura_max(criatura["id"])
    nivel_atual = _nivel_criatura(user_id, criatura["id"])
    if nivel_atual >= teto:
        return {"criatura": criatura, "era_nova": False, "nivel_novo": nivel_atual, "upou": False}

    tabela = (
        _NIVEL_CRIATURA_USOS_ACUMULADOS_ESTENDIDO
        if criatura["id"] in _NIVEL_CRIATURA_MAX_ESPECIAL
        else _NIVEL_CRIATURA_USOS_ACUMULADOS
    )
    dados.setdefault("usos_criaturas", {})
    dados["usos_criaturas"][criatura["id"]] = max(
        dados["usos_criaturas"].get(criatura["id"], 0),
        tabela[nivel_atual],   # limiar de usos mínimos pro PRÓXIMO nível
    )
    nivel_novo = _calcular_nivel_criatura(dados["usos_criaturas"][criatura["id"]], criatura["id"])
    return {"criatura": criatura, "era_nova": False, "nivel_novo": nivel_novo, "upou": True}


def _boss5_texto_ovo(membro: discord.Member, resultado_ovo: dict) -> str:
    """Monta a linha de texto que descreve o que aconteceu com o ovo de
    Kaelith de `membro`, pra ser encaixada no embed de resultado."""
    criatura = resultado_ovo["criatura"]
    info = _RARIDADES[criatura["raridade"]]
    if resultado_ovo["era_nova"]:
        return (
            f"🥚✨ O ovo de {membro.mention} choca na hora e revela {info['emoji']} "
            f"**{criatura['nome']}** (*{info['label']}*) — nova na coleção!"
        )
    if resultado_ovo["upou"]:
        return (
            f"🥚⭐ O ovo de {membro.mention} revela {info['emoji']} **{criatura['nome']}**, que "
            f"ela já tinha — a criatura sobe pro Nível de Capacidade `{resultado_ovo['nivel_novo']}`!"
        )
    return (
        f"🥚 O ovo de {membro.mention} revela {info['emoji']} **{criatura['nome']}**, mas ela já "
        f"estava no Nível de Capacidade máximo — nada mudou dessa vez."
    )


async def _boss5_premiar_vencedores(guild: discord.Guild, vencedores: list) -> list:
    """Aplica o ganho de XP de cada vencedor (a faixa mais baixa entre
    todos os bosses), ativa o Booster de XP de _BOSS5_BOOSTER_MINUTOS (10
    min — o mais longo de todos), atualiza nível e dispara o aviso de
    level up quando for o caso. Além disso, sorteia pra CADA vencedor uma
    chance (`_BOSS5_CHANCE_OVO`) de vir junto um 🥚 ovo Épico ou Lendário.
    Devolve uma lista de (membro, ganho, percentual, resultado_ovo|None)."""
    resultados = []
    for membro in vencedores:
        dados = xp_stats[membro.id]
        nivel_antigo = dados["nivel"]
        ganho, percentual = _boss5_calcular_ganho_xp(membro.id)
        dados["xp"] += ganho
        dados["nivel"], _, _ = _calcular_nivel(dados["xp"])
        if dados["nivel"] > nivel_antigo and guild is not None:
            asyncio.create_task(_anunciar_level_up(guild, membro, dados["nivel"]))
        # 🎁 Bônus de Kaelith: Booster de XP de 10 minutos (o mais longo de
        # todos os bosses) pra quem venceu.
        _conceder_xp_booster(membro.id, _BOSS5_BOOSTER_MINUTOS)

        # 🥚 Chance de ovo Épico/Lendário — só pra quem venceu.
        resultado_ovo = None
        if random.random() < _BOSS5_CHANCE_OVO:
            resultado_ovo = _boss5_conceder_ovo(membro.id)

        resultados.append((membro, ganho, percentual, resultado_ovo))

    asyncio.create_task(_salvar_xp_stats())
    asyncio.create_task(_atualizar_ranking_xp())

    for membro, ganho, percentual, resultado_ovo in resultados:
        detalhe_ovo = ""
        if resultado_ovo is not None:
            info = _RARIDADES[resultado_ovo["criatura"]["raridade"]]
            detalhe_ovo = f" + 🥚 ovo revelou {info['emoji']} {resultado_ovo['criatura']['nome']}"
        asyncio.create_task(_log_rpg(
            guild,
            "☠️ Recompensa — Kaelith",
            f"✨ **{membro.display_name}** ganhou **`{ganho}` XP** (`{percentual * 100:.1f}%`) + "
            f"⚡ Booster de XP de `{_BOSS5_BOOSTER_MINUTOS}min` por vencer Kaelith{detalhe_ovo}.",
        ))

    return resultados


async def _boss5_batalha_solo(canal: discord.TextChannel, membro: discord.Member) -> None:
    """Roda o confronto solo contra Kaelith: só 1.2% de chance de vitória —
    e se perder, não perde XP nenhum, só o orgulho."""
    try:
        criatura = _boss_criatura_mais_forte(membro.id)
        info_raridade = _RARIDADES[criatura["raridade"]]

        embed_convocacao = discord.Embed(
            title="💀👑 Um desafiante solitário ousa se apresentar!",
            description=(
                f"👽 **Renan:** ...{membro.mention} decidiu encarar Kaelith sozinho. Eu observo em "
                f"silêncio — nem eu sei se isso é coragem. {membro.display_name} convoca "
                f"{info_raridade['emoji']} **{criatura['nome']}**. É nível mítico — cuidado."
            ),
            color=info_raridade["cor"],
        )
        embed_convocacao.set_thumbnail(url=criatura["gif"])
        msg1 = await canal.send(embed=embed_convocacao)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "💀 **Kaelith:** *\"Coroas caem como folhas no outono diante da minha foice. "
                "Você nem usa uma... mas eu ainda assim vim colher.\"*"
            ),
            color=0x1c1128,
        )
        embed_batalha.set_image(url=_BOSS5_KAELITH_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        venceu = random.random() < _BOSS5_CHANCE_SOLO

        if venceu:
            resultados = await _boss5_premiar_vencedores(canal.guild, [membro])
            _, ganho, percentual, resultado_ovo = resultados[0]
            descricao = (
                f"🏆 **A CEIFADORA FOI CEIFADA!!** {membro.mention} e {info_raridade['emoji']} "
                f"**{criatura['nome']}** derrubaram **KAELITH, A CEIFADORA DOS REIS**, SOZINHOS!! "
                f"Só `{_BOSS5_CHANCE_SOLO * 100:.1f}%` de chance!! ☠️⚔️\n\n"
                f"✨ Recompensa: **`+{ganho}` XP** (`{percentual * 100:.1f}%`) + ⚡ **Booster de XP "
                f"{_BOSS5_BOOSTER_MINUTOS}min**!\n"
            )
            if resultado_ovo is not None:
                descricao += _boss5_texto_ovo(membro, resultado_ovo) + "\n"
            descricao += (
                f"\n👽 **Renan:** ...até a própria Morte hesitou por um segundo. Eu vou guardar isso. "
                "Você ceifou a Ceifadora. Isso vai virar lenda."
            )
            cor = 0xf5c542
        else:
            descricao = (
                f"💀 **Kaelith:** *\"...como sempre.\"* {info_raridade['emoji']} **{criatura['nome']}** "
                f"caiu em batalha, e {membro.mention} não conseguiu sozinho dessa vez.\n\n"
                f"🍃 Nenhum XP foi perdido — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...era esperado. Poucos sobrevivem sozinhos a uma foice dessas. Não "
                "desanime — contra ela, é muito melhor ir em grupo."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — Kaelith, a Ceifadora dos Reis")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


async def _boss5_batalha_grupo(canal: discord.TextChannel, participantes: list) -> None:
    """Roda o confronto em grupo contra Kaelith: cada participante convoca
    a criatura mais forte que já desbloqueou, e a chance de vitória cresce
    com o número (e a força) das criaturas convocadas — nível mítico,
    ligeiramente mais fácil que Dourakhar (boss2), mas ainda muito difícil."""
    try:
        convocacoes = [(p, _boss_criatura_mais_forte(p.id)) for p in participantes]

        embed_cabecalho = discord.Embed(
            title=f"⚔️ {len(convocacoes)} guerreiro(a)s ousam encarar a Ceifadora!",
            description=(
                "👽 **Renan:** ...esse time tá indo contra o nível mítico. Boa sorte pra todos."
            ),
            color=0x1c1128,
        )
        cards = _boss_cards_criaturas(convocacoes)

        # 1º lote: cabeçalho + até 9 cards (10 embeds é o limite do Discord por
        # mensagem). O resto (grupos grandes) sai em mensagens seguintes.
        lote = [embed_cabecalho] + cards[:9]
        restante = cards[9:]
        msg1 = await canal.send(embeds=lote)
        asyncio.create_task(_apagar_mensagem_depois(msg1))
        while restante:
            msg_extra = await canal.send(embeds=restante[:10])
            asyncio.create_task(_apagar_mensagem_depois(msg_extra))
            restante = restante[10:]
        await asyncio.sleep(3)

        embed_batalha = discord.Embed(
            description=(
                "💀 **Kaelith:** *\"Um exército inteiro... pra proteger reis que já estão mortos "
                "e ainda não sabem. Venham, então — a colheita será generosa hoje.\"*"
            ),
            color=0x1c1128,
        )
        embed_batalha.set_image(url=_BOSS5_KAELITH_BATALHA_GIF)
        aviso = await canal.send(embed=embed_batalha)
        await asyncio.sleep(3)
        try:
            await aviso.delete()
        except discord.HTTPException:
            pass

        chance = _boss5_chance_grupo(convocacoes)
        venceu = random.random() < chance

        if venceu:
            resultados = await _boss5_premiar_vencedores(canal.guild, participantes)
            texto_ganhos = "\n".join(
                f"✨ {membro.mention} +`{ganho}` XP (`{percentual * 100:.1f}%`) ⚡"
                for membro, ganho, percentual, _ovo in resultados
            )
            textos_ovo = "\n".join(
                _boss5_texto_ovo(membro, resultado_ovo)
                for membro, _g, _p, resultado_ovo in resultados
                if resultado_ovo is not None
            )
            descricao = (
                f"🏆 **A CEIFADORA FOI CEIFADA!!** O time de `{len(participantes)}` guerreiro(a)s "
                f"derrubou **KAELITH, A CEIFADORA DOS REIS**!! (chance da batalha: `{chance * 100:.0f}%`) "
                f"☠️⚔️\n\n"
                f"{texto_ganhos}\n\n"
                f"⚡ Todos os vencedores também ganharam um **Booster de XP de {_BOSS5_BOOSTER_MINUTOS} "
                f"minutos** (xp de call e mensagem em dobro)!"
            )
            if textos_ovo:
                descricao += f"\n\n{textos_ovo}"
            descricao += (
                f"\n\n👽 **Renan:** ...nem a própria Morte esperava perder pra formigas organizadas. "
                "Eu me curvo. Vocês ceifaram a Ceifadora — isso vai ficar na história."
            )
            cor = 0xf5c542
        else:
            mencoes = ", ".join(p.mention for p in participantes)
            descricao = (
                f"💀 **Kaelith:** *\"...voltem quando forem mais próximos da realeza que eu venho "
                f"colher.\"* Mesmo com `{len(participantes)}` guerreiro(a)s juntos (`{chance * 100:.0f}%` "
                f"de chance), a Ceifadora dos Reis foi forte demais dessa vez. {mencoes} não "
                f"conseguiram.\n\n"
                f"🍃 Ninguém perdeu XP — só a derrota amarga mesmo.\n\n"
                f"👽 **Renan:** ...nível mítico não perdoa fácil. Eu respeito a tentativa. "
                "Treinem e tentem de novo — chamem mais gente."
            )
            cor = 0x8b0000

        embed_resultado = discord.Embed(
            title="⚔️ FIM DO CONFRONTO!", description=descricao, color=cor, timestamp=discord.utils.utcnow()
        )
        embed_resultado.set_footer(text="👽 Renan — Kaelith, a Ceifadora dos Reis")
        msg2 = await canal.send(embed=embed_resultado)
        asyncio.create_task(_apagar_mensagem_depois(msg2))
    finally:
        _boss_ativo_no_canal.discard(canal.id)


class Boss5RecrutamentoView(discord.ui.View):
    """Botão único de 'Quero Participar!' que fica ativo por
    _BOSS5_TEMPO_RECRUTAMENTO segundos, juntando o time que vai enfrentar
    Kaelith em conjunto. Quando o tempo acaba, a batalha começa sozinha."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS5_TEMPO_RECRUTAMENTO)
        self.canal = canal
        self.participantes: dict = {}   # user_id -> discord.Member
        self.mensagem: discord.Message = None

    @discord.ui.button(label="⚔️ Quero Participar!", style=discord.ButtonStyle.success)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message(
                "👽 **Renan:** ...você já tá na lista.", ephemeral=True
            )
            return

        self.participantes[interaction.user.id] = interaction.user
        button.label = f"⚔️ Quero Participar! ({len(self.participantes)})"
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass

        participantes = list(self.participantes.values())
        if not participantes:
            try:
                msg = await self.canal.send(
                    "👽 **Renan:** ...ninguém teve coragem de se juntar a tempo. Kaelith sorri e "
                    "se dissolve... por enquanto."
                )
                asyncio.create_task(_apagar_mensagem_depois(msg))
            finally:
                _boss_ativo_no_canal.discard(self.canal.id)
            return

        asyncio.create_task(_boss5_batalha_grupo(self.canal, participantes))


class Boss5EscolhaView(discord.ui.View):
    """Botões de 'Todos Juntos' e 'Eu Consigo Sozinho' que aparecem quando
    Kaelith surge. A PRIMEIRA escolha feita (por qualquer pessoa) decide
    o caminho dessa aparição do boss."""

    def __init__(self, canal: discord.TextChannel):
        super().__init__(timeout=_BOSS5_TEMPO_ESCOLHA)
        self.canal = canal
        self.decidido = False
        self.mensagem: discord.Message = None

    def _travar_botoes(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="🤝 Todos Juntos", style=discord.ButtonStyle.primary)
    async def todos_juntos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🤝 O CHAMADO FOI FEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} decidiu enfrentar Kaelith em grupo. "
                f"Quem tiver coragem, clique no botão abaixo. `{_BOSS5_TEMPO_RECRUTAMENTO}s` pra se "
                "juntar ao time."
            ),
            color=0xff8800,
        )
        embed.set_image(url=_BOSS5_KAELITH_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        view_recrutamento = Boss5RecrutamentoView(self.canal)
        msg_recrutamento = await self.canal.send(
            "☠️ Time contra **Kaelith, a Ceifadora dos Reis** — clique pra participar!",
            view=view_recrutamento,
        )
        view_recrutamento.mensagem = msg_recrutamento
        asyncio.create_task(_apagar_mensagem_depois(msg_recrutamento))

    @discord.ui.button(label="🗡️ Eu Consigo Sozinho", style=discord.ButtonStyle.danger)
    async def sozinho(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.bot:
            return
        if self.decidido:
            await interaction.response.send_message(
                "👽 **Renan:** ...essa decisão já foi tomada.", ephemeral=True
            )
            return
        self.decidido = True
        self._travar_botoes()
        self.stop()

        embed = discord.Embed(
            title="🗡️ DESAFIO SOLITÁRIO ACEITO!",
            description=(
                f"👽 **Renan:** ...{interaction.user.mention} escolheu encarar Kaelith sozinho. "
                "Isso não é coragem, isso é desafiar a própria Morte de frente. Só "
                f"`{_BOSS5_CHANCE_SOLO * 100:.1f}%` de chance — é nível mítico, tem certeza?"
            ),
            color=0xff4444,
        )
        embed.set_image(url=_BOSS5_KAELITH_INTRO_GIF)
        await interaction.response.edit_message(embed=embed, view=self)

        asyncio.create_task(_boss5_batalha_solo(self.canal, interaction.user))

    async def on_timeout(self):
        if self.decidido or self.mensagem is None:
            return
        self._travar_botoes()
        try:
            embed = discord.Embed(
                title="⚰️ Kaelith se dissolve nas sombras...",
                description=(
                    "👽 **Renan:** ...ninguém teve coragem de decidir a tempo. A Ceifadora dos "
                    "Reis se retira... por enquanto."
                ),
                color=0x888888,
            )
            await self.mensagem.edit(embed=embed, view=self)
        except discord.HTTPException:
            pass
        _boss_ativo_no_canal.discard(self.canal.id)


@bot.command(name="boss5")
async def cmd_boss5(ctx):
    """☠️👑 Invoca Kaelith, a Ceifadora dos Reis — nível mítico, ligeiramente
    mais fraca que Dourakhar (boss2, o boss mais forte de todos), mas ainda
    um dos bosses mais difíceis do servidor. Só o Reality (CRIADOR_ID) pode
    chamar. O chat escolhe entre encarar sozinho (~1.2% de chance) ou juntar
    um time (mais gente = mais chance). Quem vencer ganha o XP mais modesto
    entre todos os bosses, mas leva um Booster de XP de 10 minutos — o mais
    longo de todos — e tem 35% de chance de vir junto um 🥚 ovo aleatório
    entre criaturas Épicas e Lendárias (se for repetido, a criatura sobe de
    Nível de Capacidade em vez de não fazer nada). Uso: .boss5"""
    if ctx.author.id != CRIADOR_ID:
        return

    try:
        await ctx.message.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if guild is None:
        return
    canal = guild.get_channel(_BOSS5_CANAL_ID)
    if canal is None:
        return

    if canal.id in _boss_ativo_no_canal:
        aviso = await ctx.send(
            "👽 **Renan:** ...já tem um boss ativo por lá. Espere esse terminar."
        )
        asyncio.create_task(_apagar_mensagem_depois(aviso))
        return

    _boss_ativo_no_canal.add(canal.id)

    embed = discord.Embed(
        title="☠️👑 NÍVEL MÍTICO — KAELITH, A CEIFADORA DOS REIS, DESPERTOU!!",
        description=(
            "👽 **Renan:** ...o silêncio chega antes dela. Nem o vento ousa se mexer.\n\n"
            "💀 **Kaelith:** *\"Eu sou Kaelith. Reis, impérios, coroas... tudo cai perante minha "
            "foice, mais cedo ou mais tarde. Vocês não são diferentes.\"*\n\n"
            "Isso aqui também é nível **mítico**. Ela é só um pouquinho mais fraca que Dourakhar, "
            "mas ainda muito perigosa. Sozinho ou em grupo?\n\n"
            f"⏳ Vocês têm `{_BOSS5_TEMPO_ESCOLHA}s` pra decidir."
        ),
        color=0x1c1128,
    )
    embed.set_image(url=_BOSS5_KAELITH_INTRO_GIF)
    embed.set_footer(text="👽 Renan — Nível Mítico: Kaelith, a Ceifadora dos Reis")

    view = Boss5EscolhaView(canal)
    msg = await canal.send(embed=embed, view=view)
    view.mensagem = msg
    asyncio.create_task(_apagar_mensagem_depois(msg))


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
            "`.tocar <link/nome>` — toca ou enfileira uma música "
            "(YouTube, Spotify, SoundCloud, playlists inteiras)\n"
            "`.setup` — reenvia o painel de música pra esse canal\n"
            "`.letras` — link direto pra letra da música tocando agora\n"
            "`.sair` — para tudo, limpa a fila, eu vou embora "
            "(aliases: `.parar`, `.stop`)"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎭 Cargos",
        value=(
            f"Painéis de cargos por reação em <#{CANAL_CARGOS_ID}> — "
            "reaja pra pegar, tire a reação pra perder."
        ),
        inline=False,
    )
    embed.add_field(
        name="🎫 Atendimento",
        value=(
            f"Painel de tickets em <#{CANAL_PAINEL_TICKET_ID}> — clique em "
            "**Abrir Ticket** pra falar com a staff em particular.\n"
            "Só a staff pode clicar em **Fechar Ticket**.\n"
            "`.feedback` (staff) — dentro de um ticket aberto, manda pro "
            "dono o pedido de avaliação do atendimento."
        ),
        inline=False,
    )
    embed.add_field(
        name="🔢 Contagem",
        value=(
            f"Em <#{CANAL_CONTAGEM_ID}>: conta em sequência, um número por "
            "vez, sem repetir. Acertou, 👍. Errou, zera e eu mostro minha cara."
        ),
        inline=False,
    )
    embed.add_field(
        name="🎂 Aniversário",
        value=(
            f"Em <#{CANAL_ANIVERSARIO_REGISTRO_ID}>: manda sua data no formato "
            "`DD/MM` que eu guardo. Manda outra data e eu pergunto antes de trocar. "
            f"No dia, eu aviso em <#{CANAL_ANIVERSARIO_ANUNCIO_ID}>."
        ),
        inline=False,
    )
    embed.add_field(
        name="💌 Convites",
        value="Todo mundo que entra usando um convite fica registrado, com quem convidou e o total acumulado.",
        inline=False,
    )
    embed.add_field(
        name="👽 Sobre",
        value="`.sobre` — quem eu sou, se você não sabia",
        inline=False,
    )
    embed.set_footer(text="Prefixo: !")
    await ctx.send(embed=embed)


# ══════════════════════════════════════════════
# EVENTOS
# ══════════════════════════════════════════════

_cargos_configurados = False


@bot.event
async def on_ready():
    print(f"[Renan] conectado como {bot.user} ({bot.user.id})")
    try:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="a realidade bater")
        )
    except discord.HTTPException:
        pass

    global _cargos_configurados
    if not _cargos_configurados:
        try:
            await _configurar_cargos_reacao()
        except Exception as e:
            print(f"[renan-cargos] erro ao configurar cargos: {e!r}")
        try:
            await _configurar_regras()
        except Exception as e:
            print(f"[renan-regras] erro ao configurar regras: {e!r}")
        try:
            bot.add_view(PainelTicket())   # registra os botões como persistentes
            bot.add_view(FecharTicket())   # (funcionam mesmo depois de reiniciar o bot)
            dados_tickets = _carregar_dados_tickets()
            for chave, registro in dados_tickets.get("pendentes_feedback", {}).items():
                if not registro.get("enviado"):
                    bot.add_view(_ViewAvaliarAtendimento(int(chave)))
            await _configurar_painel_ticket()
        except Exception as e:
            print(f"[renan-ticket] erro ao configurar painel de atendimento: {e!r}")
        try:
            dados_sugestoes = _carregar_dados_sugestoes()
            for sug_id in dados_sugestoes.keys():
                bot.add_view(_ViewSugestao(sug_id))   # re-registra os botões ✅/❌ de cada sugestão salva
        except Exception as e:
            print(f"[renan-sugestoes] erro ao re-registrar botões de sugestões: {e!r}")
        _cargos_configurados = True  # não repete a cada reconexão, só na 1ª vez

    for guild in bot.guilds:
        try:
            await _atualizar_cache_convites(guild)
        except Exception as e:
            print(f"[renan-convites] erro ao montar cache de convites de {guild.name}: {e!r}")

    if not _checar_aniversarios_loop.is_running():
        _checar_aniversarios_loop.start()

    # ── RPG: XP/Ranking de Nível + Batalha de Criaturas + Bosses ───────────
    global _xp_stats_lock, _xp_ranking_update_lock
    if _xp_stats_lock is None:
        _xp_stats_lock = asyncio.Lock()
    if _xp_ranking_update_lock is None:
        _xp_ranking_update_lock = asyncio.Lock()

    if not loop_ranking_xp.is_running():
        loop_ranking_xp.start()

    # Reconcilia a streak do Booster de Call salva em disco com quem
    # REALMENTE está numa call válida e desmutada agora (ver comentário
    # completo na versão original, no bloco do Booster de Call).
    _membros_elegiveis_call_booster: set = set()
    for guild in bot.guilds:
        for canal_voz in guild.voice_channels:
            if canal_voz.id in _XP_CALLS_PRIVADAS:
                continue
            for membro in canal_voz.members:
                if membro.bot:
                    continue
                estado_voz = membro.voice
                if estado_voz is not None and (estado_voz.self_mute or estado_voz.mute):
                    continue
                _membros_elegiveis_call_booster.add(membro.id)

    for uid in list(_call_booster_inicio.keys()):
        if uid not in _membros_elegiveis_call_booster:
            _resetar_call_booster(uid)

    for uid in _membros_elegiveis_call_booster:
        _call_booster_inicio.setdefault(uid, time.time())

    asyncio.create_task(_salvar_call_booster_stats())

    if not loop_checar_ovos.is_running():
        loop_checar_ovos.start()

    if not loop_checar_ovos_dragao.is_running():
        loop_checar_ovos_dragao.start()

    bot.add_view(RankingXPView(total_paginas=2))
    bot.add_view(CorQuadradoView())
    bot.add_view(EnciclopediaView())
    # ─────────────────────────────────────────────────────────────────────


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
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    """RPG: Booster de Call (streak de xp em call) e a contagem de tempo dos
    Ovos pendentes (.ovo / .ovodragao) — roda isolado pra nunca quebrar
    nenhuma outra funcionalidade do bot."""
    if member.bot:
        return

    try:
        await _processar_call_booster_voice(member, before, after)
    except Exception as e:
        print(f"[renan-callbooster] erro para {member}: {e!r}")

    try:
        if member.id in _ovos_pendentes:
            entrou_em_call = before.channel is None and after.channel is not None
            saiu_da_call = before.channel is not None and after.channel is None
            if entrou_em_call:
                _ovo_iniciar_contagem(member.id)
            elif saiu_da_call:
                _ovo_pausar_contagem(member.id)

        if member.id in _ovos_dragao_pendentes:
            entrou_em_call = before.channel is None and after.channel is not None
            saiu_da_call = before.channel is not None and after.channel is None
            if entrou_em_call:
                _ovo_dragao_iniciar_contagem(member.id)
            elif saiu_da_call:
                _ovo_dragao_pausar_contagem(member.id)
    except Exception as e:
        print(f"[renan-ovo] erro ao processar ovo pendente de {member}: {e!r}")


@bot.event
async def on_member_join(member: discord.Member):
    """Boas-vindas no canal dedicado, no estilo frio (mas não indiferente)
    do Renan: um único embed com avatar do membro, contagem do servidor,
    o banner de boas-vindas e os direcionamentos pra registro e regras.
    Também loga, separadamente, qual convite foi usado pra entrar."""
    canal = member.guild.get_channel(CANAL_BOAS_VINDAS_ID)
    if canal is not None:
        descricao = (
            f"{member.mention} {random.choice(FRASES_BOAS_VINDAS)}\n\n"
            f"Antes de mais nada: passa em <#{CANAL_CARGOS_ID}> pra fazer seu "
            f"registro adicional, e não deixa de ler as <#{CANAL_REGRAS_ID}> "
            f"— regras existem mesmo quando o mundo já acabou uma vez."
        )

        embed = discord.Embed(
            title="👽 Mais um sinal de vida chegou",
            description=descricao,
            color=COR_RENAN,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=IMAGEM_BOAS_VINDAS)
        embed.add_field(name="Agora somos", value=f"{member.guild.member_count} por aqui", inline=True)
        embed.set_footer(text="Renan está observando.")

        try:
            await canal.send(embed=embed)
        except discord.HTTPException:
            pass

    try:
        await _logar_convite_usado(member)
    except Exception as e:
        print(f"[renan-convites] erro ao logar convite de {member}: {e!r}")



@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Auto-play: link solto de música (YouTube/Spotify/SoundCloud) já
    # entra direto na fila, sem precisar de .tocar na frente.
    try:
        await _processar_link_solto(message)
    except Exception as e:
        print(f"[renan-musica] erro ao processar link solto de {message.author}: {e!r}")

    # Jogo de contagem — canal dedicado, número certo = 👍, errou = zera
    try:
        await _processar_contagem(message)
    except Exception as e:
        print(f"[renan-contagem] erro ao processar contagem de {message.author}: {e!r}")

    # Aniversários — canal dedicado, DD/MM cadastra (ou pede confirmação pra trocar)
    try:
        await _processar_aniversario(message)
    except Exception as e:
        print(f"[renan-aniversario] erro ao processar aniversário de {message.author}: {e!r}")

    # Sugestões — canal dedicado, mensagem vira embed com votação ✅/❌
    try:
        await _processar_sugestao(message)
    except Exception as e:
        print(f"[renan-sugestoes] erro ao processar sugestão de {message.author}: {e!r}")

    # Personalidade — respostas curtas e frias a gatilhos de conversa
    await _checar_personalidade(message)

    # RPG: Ranking de Nível (XP) — ganho por mensagem, com cooldown
    try:
        await _processar_xp_mensagem(message)
    except Exception as e:
        print(f"[renan-xp] erro ao processar XP de {message.author}: {e!r}")

    # RPG: Batalha de Criaturas — gatilho "eu te desafio @alguém"
    try:
        await _processar_desafio(message)
    except Exception as e:
        print(f"[renan-batalha] erro ao processar desafio de {message.author}: {e!r}")

    await bot.process_commands(message)


# ══════════════════════════════════════════════
# START
# ══════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(TOKEN)
