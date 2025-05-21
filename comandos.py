from discord import app_commands
import discord
import yt_dlp
import asyncio
import random

playlist_queues = {}
playlist_settings = {}

async def play_next(ctx, guild_id, loop=None):
    queue = playlist_queues.get(guild_id, [])
    settings = playlist_settings.get(guild_id, {"loop": None, "shuffle": False, "original": []})
    if not queue:
        embed = discord.Embed(
            title="🎶 Playlist finalizada!",
            description="A playlist chegou ao fim!",
            color=discord.Color.red()
        )
        await ctx.channel.send(embed=embed)
        # Loop de playlist
        if settings.get("loop") == "playlist" and settings.get("original"):
            queue = settings["original"].copy()
            playlist_queues[guild_id] = queue
            # Precisa garantir que vc está definido antes de tentar tocar novamente
            vc = ctx.guild.voice_client
            if not vc:
                return
        else:
            return
    vc = ctx.guild.voice_client
    if not vc or not queue:
        return
    # Shuffle se ativado
    if settings.get("shuffle") and len(queue) > 1:
        random.shuffle(queue)
    url, title = queue[0]
    # Loop de música: não remove da fila
    if settings.get("loop") == "musica":
        pass
    else:
        queue.pop(0)
    playlist_queues[guild_id] = queue
    if loop is None:
        loop = asyncio.get_running_loop()
    def after_playing(error=None):
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx, guild_id, loop), loop)
        try:
            fut.result()
        except Exception:
            pass
    source = discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
    vc.play(source, after=after_playing)
    embed = discord.Embed(
        title="🎵 Tocando agora",
        description=f"**{title}**",
        color=discord.Color.green()
    )
    asyncio.run_coroutine_threadsafe(ctx.channel.send(embed=embed), loop)

def setup_commands(tree: app_commands.CommandTree):
    @tree.command(name="ping", description="Responde com pong!")
    async def ping_slash(interaction):
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="join", description="Faz o bot entrar na call em que você está.")
    async def join_slash(interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(description="❌ Você precisa estar em um canal de voz.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        embed = discord.Embed(description=f"✅ Entrei na call: {channel.mention}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="loop", description="Ativa/desativa o loop da playlist ou música.")
    @app_commands.describe(tipo="Tipo de loop: playlist ou musica")
    async def loop_slash(interaction: discord.Interaction, tipo: str):
        gid = interaction.guild.id
        settings = playlist_settings.setdefault(gid, {"loop": None, "shuffle": False, "original": []})
        if tipo not in ["playlist", "musica"]:
            embed = discord.Embed(description="❌ Use `/loop playlist` ou `/loop musica`.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if settings["loop"] == tipo:
            settings["loop"] = None
            embed = discord.Embed(description=f"🔁 Loop {tipo} desativado!", color=discord.Color.blurple())
        else:
            settings["loop"] = tipo
            embed = discord.Embed(description=f"🔁 Loop {tipo} ativado!", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="aleatorio", description="Ativa/desativa o modo aleatório (shuffle) da playlist.")
    async def aleatorio_slash(interaction: discord.Interaction):
        gid = interaction.guild.id
        settings = playlist_settings.setdefault(gid, {"loop": None, "shuffle": False, "original": []})
        settings["shuffle"] = not settings["shuffle"]
        embed = discord.Embed(
            description=f"🔀 Aleatório {'ativado' if settings['shuffle'] else 'desativado'}!",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="tocar", description="Toca música ou playlist do YouTube, Spotify ou nome.")
    @app_commands.describe(query="Link, playlist ou nome da música")
    async def tocar_slash(interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(description="❌ Você precisa estar em um canal de voz.", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            return
        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client
        if not vc:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)
        # Se for link do Spotify, buscar nome da música
        if "spotify.com" in query:
            embed = discord.Embed(description="🔎 Buscando música do Spotify no YouTube...", color=discord.Color.blurple())
            await interaction.followup.send(embed=embed)
            import requests
            import re
            try:
                r = requests.get(query)
                title = re.search(r'<title>(.*?)</title>', r.text)
                if title:
                    query = title.group(1).replace(" - song and lyrics by Spotify", "").replace(" | Spotify", "").strip()
            except Exception:
                embed = discord.Embed(description="❌ Não foi possível buscar a música do Spotify.", color=discord.Color.red())
                await interaction.followup.send(embed=embed)
                return
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'extract_flat': False,
            'default_search': 'ytsearch',
        }
        queue = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    # Limita a 20 músicas para evitar erro de recursão
                    for entry in info['entries'][:20]:
                        if entry and 'url' in entry:
                            queue.append((entry['url'], entry.get('title', 'Música')))
                else:
                    queue.append((info['url'], info.get('title', 'Música')))
        except Exception as e:
            embed = discord.Embed(description=f"❌ Erro ao buscar/tocar: {e}", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            return
        if not queue:
            embed = discord.Embed(description="❌ Nenhuma música encontrada.", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            return
        playlist_queues[interaction.guild.id] = queue.copy()
        playlist_settings[interaction.guild.id] = playlist_settings.get(interaction.guild.id, {"loop": None, "shuffle": False, "original": []})
        playlist_settings[interaction.guild.id]["original"] = queue.copy()
        if len(queue) == 1:
            embed = discord.Embed(title="🎵 Tocando agora", description=f"**{queue[0][1]}**", color=discord.Color.green())
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(title="🎶 Playlist adicionada!", description=f"Tocando agora: **{queue[0][1]}**", color=discord.Color.blurple())
            await interaction.followup.send(embed=embed)
        if not vc.is_playing():
            loop = asyncio.get_running_loop()
            await play_next(interaction, interaction.guild.id, loop)

    @tree.command(name="pular", description="Pula para a próxima música da fila.")
    async def pular_slash(interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            embed = discord.Embed(description="❌ Não estou tocando nada.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        vc.stop()
        embed = discord.Embed(description="⏭️ Pulando para a próxima música...", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="stop", description="Para a música e limpa a fila.")
    async def stop_slash(interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
        playlist_queues[interaction.guild.id] = []
        # Limpa também o histórico da playlist para evitar reuso de links antigos
        if interaction.guild.id in playlist_settings:
            playlist_settings[interaction.guild.id]["original"] = []
        embed = discord.Embed(description="⏹️ Música parada e fila limpa!", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="pause", description="Pausa a música atual.")
    async def pause_slash(interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            embed = discord.Embed(description="❌ Não estou tocando nada.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        vc.pause()
        embed = discord.Embed(description="⏸️ Música pausada!", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="play", description="Retoma a música pausada.")
    async def play_slash(interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_paused():
            embed = discord.Embed(description="❌ Não há música pausada.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        vc.resume()
        embed = discord.Embed(description="▶️ Música retomada!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="voltar", description="Volta para a música anterior da fila.")
    async def voltar_slash(interaction: discord.Interaction):
        gid = interaction.guild.id
        settings = playlist_settings.get(gid, {"loop": None, "shuffle": False, "original": []})
        queue = playlist_queues.get(gid, [])
        original = settings.get("original", [])
        vc = interaction.guild.voice_client
        if not original or len(original) < 2:
            embed = discord.Embed(description="❌ Não há música anterior para voltar.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # Descobre a música atual
        tocando = None
        if vc and vc.is_playing():
            tocando = queue[0] if queue else None
        # Descobre o índice da música atual na original
        idx = 0
        if tocando and tocando in original:
            idx = original.index(tocando)
        elif queue and queue[0] in original:
            idx = original.index(queue[0])
        # Volta uma música (ou para o início se já for a primeira)
        idx = max(idx - 1, 0)
        # Atualiza a fila para começar da música anterior
        playlist_queues[gid] = original[idx:]
        if vc:
            vc.stop()
        embed = discord.Embed(description=f"⏮️ Voltando para: **{original[idx][1]}**", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)
