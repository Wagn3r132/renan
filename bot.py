import discord
from discord.ext import commands, tasks
import random
import os
import re
import json
import time
import asyncio
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
    if message.guild is None:
        return  # DM não tem estado de voz (message.author aqui é User, não Member)

    if message.author.voice is None or message.author.voice.channel is None:
        return  # ninguém numa call, ignora silenciosamente

    # Se a mensagem já é um comando válido (ex.: "!tocar <link>"), quem
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
# FEEDBACK: a staff usa `!feedback` dentro do ticket (antes de fechar)
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
            "Esse canal não é um ticket aberto — o `!feedback` só funciona "
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

# guild_id (str) -> {"numero_atual": int, "ultimo_usuario_id": int|None, "recorde": int}
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
        }
    return _contagem_estado[guild_id]


def _salvar_estado_contagem(guild_id: int) -> None:
    dados = _carregar_dados_contagem()
    dados[str(guild_id)] = _contagem_estado[guild_id]
    _salvar_dados_contagem(dados)


async def _processar_contagem(message: discord.Message) -> None:
    """Confere uma mensagem no canal de contagem. Só reage a mensagens
    que são só um número — o resto passa batido, sem quebrar a
    sequência."""
    if message.guild is None or message.channel.id != CANAL_CONTAGEM_ID:
        return

    texto = message.content.strip()
    if not texto.isdigit():
        return

    numero = int(texto)
    estado = _estado_contagem(message.guild.id)
    esperado = estado["numero_atual"] + 1

    # erra se: número fora de sequência, OU a mesma pessoa contando
    # duas vezes seguidas (regra clássica desse tipo de jogo)
    errou = numero != esperado or message.author.id == estado["ultimo_usuario_id"]

    if errou:
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
    _salvar_estado_contagem(message.guild.id)

    try:
        await message.add_reaction("👍")
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
            "`!feedback` (staff) — dentro de um ticket aberto, manda pro "
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
        value="`!sobre` — quem eu sou, se você não sabia",
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
        _cargos_configurados = True  # não repete a cada reconexão, só na 1ª vez

    for guild in bot.guilds:
        try:
            await _atualizar_cache_convites(guild)
        except Exception as e:
            print(f"[renan-convites] erro ao montar cache de convites de {guild.name}: {e!r}")

    if not _checar_aniversarios_loop.is_running():
        _checar_aniversarios_loop.start()


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
    # entra direto na fila, sem precisar de !tocar na frente.
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

    # Personalidade — respostas curtas e frias a gatilhos de conversa
    await _checar_personalidade(message)

    await bot.process_commands(message)


# ══════════════════════════════════════════════
# START
# ══════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(TOKEN)
