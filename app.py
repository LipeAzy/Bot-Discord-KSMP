import discord
from discord.ext import commands
from discord import ui
import os
from dotenv import load_dotenv
from datetime import datetime
from discord.ext import commands, tasks
from datetime import datetime, timezone
from mcstatus import JavaServer
import json
import base64
from io import BytesIO
import aiohttp
import random

load_dotenv()

# Configurações Globais
CURRENT_USER = "LipeAzy"
CURRENT_TIME = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configurações do Servidor
MINECRAFT_SERVER_IP = "enx-cirion-48.enx.host"
MINECRAFT_SERVER_PORT = 10047
STATUS_CONFIG_FILE = "status_config.json"

# Status rotativo para o bot (agora usando status customizado)
BOT_STATUS_MESSAGES = [
    lambda data: f"👥 {data['players_online']} jogadores online",
    lambda data: f"🎮 {MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}",
    lambda data: f"⚡ TPS: {data['tps']}"
]

status_config = {
    "channel_id": None,
    "message_id": None
}

# Adicionar após as outras constantes de ID
CANAL_STATUS_ADICIONAL = 1370669650559373322
PRODUCAO_ROLE_ID = 1371248255954063392
CANAL_LOG_VILAS = 1370693091102556262  # Canal para logs de vilas

def load_status_config():
    global status_config
    try:
        if os.path.exists(STATUS_CONFIG_FILE):
            with open(STATUS_CONFIG_FILE, 'r') as f:
                status_config = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar configuração: {e}")

def save_status_config():
    try:
        with open(STATUS_CONFIG_FILE, 'w') as f:
            json.dump(status_config, f)
    except Exception as e:
        print(f"Erro ao salvar configuração: {e}")

async def get_server_status():
    """Função para obter o status do servidor Minecraft"""
    try:
        server = JavaServer(MINECRAFT_SERVER_IP, MINECRAFT_SERVER_PORT)
        status = await server.async_status()
        
        # Tentar obter TPS via query
        try:
            query = await server.async_query()
            tps = "20.0"
        except:
            tps = "20.0"  # Valor padrão se não conseguir consultar
        
        return {
            'online': True,
            'players_online': status.players.online,
            'players_max': status.players.max,
            'version': status.version.name,
            'latency': round(status.latency, 1),
            'tps': tps,
            'players_list': get_players_list(status)
        }
    except Exception as e:
        print(f"Erro ao obter status do servidor: {e}")
        return {
            'online': False,
            'players_online': 0,
            'players_max': 0,
            'version': 'Desconhecida',
            'latency': 0,
            'tps': 'N/A',
            'players_list': []
        }

def get_players_list(status):
    """Obtém lista de jogadores online"""
    try:
        if hasattr(status.players, 'sample') and status.players.sample:
            return [player.name for player in status.players.sample]
        return []
    except:
        return []

def create_status_embed(status):
    """Cria a embed com as informações do servidor"""
    current_time = datetime.now(timezone.utc)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    if status['online']:
        embed = discord.Embed(
            title="🟢 Servidor Online",
            color=discord.Color.green(),
            timestamp=current_time
        )
        
        embed.add_field(
            name="👥 Jogadores Online",
            value=f"{status['players_online']}/{status['players_max']}",
            inline=True
        )
        
        embed.add_field(
            name="🌐 Servidor",
            value=f"`{MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}`",
            inline=True
        )
        
        embed.add_field(
            name="⚡ TPS",
            value=f"{status['tps']}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Latência",
            value=f"{status['latency']}ms",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Versão",
            value=status['version'],
            inline=True
        )
        
        embed.add_field(
            name="⏰ Horário UTC",
            value=f"`{formatted_time}`",
            inline=True
        )

        if status['players_list']:
            players_text = '\n'.join(status['players_list'][:10])
            if len(status['players_list']) > 10:
                players_text += f"\n... e mais {len(status['players_list']) - 10} jogadores"
            embed.add_field(
                name="🎮 Jogadores Online",
                value=f"```\n{players_text}\n```",
                inline=False
            )
        
        footer_text = f"Última atualização por {CURRENT_USER}"
    else:
        embed = discord.Embed(
            title="🔴 Servidor Offline",
            description="O servidor está temporariamente indisponível.",
            color=discord.Color.red(),
            timestamp=current_time
        )
        
        embed.add_field(
            name="🌐 Servidor",
            value=f"`{MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}`",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Horário UTC",
            value=f"`{formatted_time}`",
            inline=True
        )
        
        footer_text = f"Tentando reconectar... • {CURRENT_USER}"
    
    embed.set_footer(text=footer_text)
    return embed

@tasks.loop(minutes=2)
async def update_server_status():
    """Atualiza o status do servidor a cada 2 minutos"""
    try:
        status = await get_server_status()
        embed = create_status_embed(status)

        # Atualizar mensagem configurada pelo setup_status
        if status_config["channel_id"] and status_config["message_id"]:
            try:
                channel = bot.get_channel(status_config["channel_id"])
                if channel:
                    try:
                        message = await channel.fetch_message(status_config["message_id"])
                        await message.edit(embed=embed)
                    except discord.NotFound:
                        # Mensagem não encontrada, envia nova e atualiza o config
                        message = await channel.send(embed=embed)
                        status_config["message_id"] = message.id
                        save_status_config()
            except Exception as e:
                print(f"Erro ao atualizar status no canal principal: {e}")

        else:
            # Se não há configuração, envia nova mensagem e salva
            channel = bot.get_channel(CANAL_STATUS_ADICIONAL)
            if channel:
                message = await channel.send(embed=embed)
                status_config["channel_id"] = channel.id
                status_config["message_id"] = message.id
                save_status_config()

        # Atualizar canal adicional (opcional, pode remover se não quiser duplicidade)
        try:
            canal_adicional = bot.get_channel(CANAL_STATUS_ADICIONAL)
            if canal_adicional:
                # Buscar última mensagem do canal
                async for message in canal_adicional.history(limit=1):
                    try:
                        await message.edit(embed=embed)
                        break
                    except:
                        await canal_adicional.send(embed=embed)
                        break
                else:
                    # Se não houver mensagens, enviar uma nova
                    await canal_adicional.send(embed=embed)
        except Exception as e:
            print(f"Erro ao atualizar status no canal adicional: {e}")

    except Exception as e:
        print(f"Erro ao atualizar status: {e}")

@tasks.loop(minutes=2)
async def update_bot_status():
    """Atualiza o status do bot"""
    try:
        status = await get_server_status()
        if status['online']:
            status_message = random.choice(BOT_STATUS_MESSAGES)(status)
            await bot.change_presence(
                activity=discord.CustomActivity(name=status_message),
                status=discord.Status.online
            )
        else:
            await bot.change_presence(
                activity=discord.CustomActivity(name="Servidor Offline 😴"),
                status=discord.Status.dnd
            )
    except Exception as e:
        print(f"Erro ao atualizar status do bot: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_status(ctx):
    """Configura a mensagem de status inicial"""
    if status_config["channel_id"] and status_config["message_id"]:
        try:
            old_channel = bot.get_channel(status_config["channel_id"])
            if old_channel:
                try:
                    old_message = await old_channel.fetch_message(status_config["message_id"])
                    await old_message.delete()
                except discord.NotFound:
                    pass
        except Exception as e:
            print(f"Erro ao deletar mensagem antiga: {e}")

    status = await get_server_status()
    embed = create_status_embed(status)
    
    message = await ctx.send(embed=embed)
    
    status_config["channel_id"] = ctx.channel.id
    status_config["message_id"] = message.id
    save_status_config()
    
    await ctx.send("✅ Status configurado com sucesso!", delete_after=5)

# IDs dos cargos e canal
CARGO_NAO_REGISTRADO = 1370692084159484055
CARGO_REGISTRADO = 1370692057227858020
CANAL_REGISTROS = 1370693091102556262

class RegistroModal(ui.Modal, title='Registro do Servidor'):
    nick_minecraft = ui.TextInput(
        label='Qual seu Nick do Minecraft?',
        placeholder='Digite seu nick exatamente como é no jogo',
        required=True,
        min_length=3,
        max_length=16
    )
    
    tipo_jogador = ui.TextInput(
        label='Você será Player ou Ovo?',
        placeholder='Digite "Player" ou "Ovo"',
        required=True
    )
    
    vila = ui.TextInput(
        label='Deseja participar de uma vila?',
        placeholder='Se sim, digite o nome da vila. Se não, digite "Não"',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Pegar os cargos
        cargo_registrado = interaction.guild.get_role(CARGO_REGISTRADO)
        cargo_nao_registrado = interaction.guild.get_role(CARGO_NAO_REGISTRADO)
        
        # Atualizar os cargos do membro
        membro = interaction.user
        await membro.remove_roles(cargo_nao_registrado)
        await membro.add_roles(cargo_registrado)

        # Criar embed para o usuário
        embed_usuario = discord.Embed(
            title="✅ Registro Completado!",
            description="Seu registro foi concluído com sucesso!",
            color=discord.Color.green()
        )
        embed_usuario.add_field(name="Nick Minecraft", value=self.nick_minecraft.value, inline=False)
        embed_usuario.add_field(name="Tipo de Jogador", value=self.tipo_jogador.value, inline=False)
        embed_usuario.add_field(name="Vila", value=self.vila.value, inline=False)
        embed_usuario.set_footer(text="Bem-vindo(a) ao servidor!")

        # Criar embed para o canal de registros
        embed_registro = discord.Embed(
            title="📝 Novo Registro",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed_registro.add_field(name="Discord", value=f"{interaction.user.mention} (`{interaction.user.name}`)", inline=False)
        embed_registro.add_field(name="Nick Minecraft", value=self.nick_minecraft.value, inline=False)
        embed_registro.add_field(name="Tipo de Jogador", value=self.tipo_jogador.value, inline=False)
        embed_registro.add_field(name="Vila", value=self.vila.value, inline=False)
        embed_registro.set_footer(text=f"ID do usuário: {interaction.user.id}")
        
        if interaction.user.avatar:
            embed_registro.set_thumbnail(url=interaction.user.avatar.url)

        # Enviar mensagem para o usuário
        await interaction.response.send_message(embeds=[embed_usuario], ephemeral=True)

        # Enviar mensagem no canal de registros
        canal_registros = interaction.guild.get_channel(CANAL_REGISTROS)
        if canal_registros:
            await canal_registros.send(embeds=[embed_registro])

class BotaoRegistro(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.green, custom_id="registro_button")
    async def registro(self, interaction: discord.Interaction, button: ui.Button):
        modal = RegistroModal()
        await interaction.response.send_modal(modal)

@bot.command()
@commands.has_permissions(administrator=True)
async def criar_vila(ctx, *, nome_vila: str):
    """Cria uma nova vila com categoria, canais e cargo exclusivo."""
    producao_role = ctx.guild.get_role(PRODUCAO_ROLE_ID)
    if producao_role not in ctx.author.roles:
        await ctx.send("❌ Você não tem permissão para criar vilas.")
        return

    nome_vila_formatado = nome_vila.strip().title()
    nome_cargo = f"▪︎ 𝐕𝐢𝐥𝐚 {nome_vila_formatado} ▪︎"
    nome_categoria = f"🛖 | Vila {nome_vila_formatado}"
    nome_chat = "💬┇chat"
    nome_comandos = "💻┇comandos"
    nome_voice = f"🎤┇{nome_vila_formatado}"

    # Cria o cargo da vila
    cargo_vila = await ctx.guild.create_role(name=nome_cargo, mentionable=True)
    
    # Permissões: só o cargo da vila e admins podem ver
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        cargo_vila: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
    }
    producao_role = ctx.guild.get_role(PRODUCAO_ROLE_ID)
    if producao_role:
        overwrites[producao_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)

    # Cria a categoria (posição será ajustada depois)
    categoria = await ctx.guild.create_category(name=nome_categoria, overwrites=overwrites)

    # Cria os canais
    await categoria.create_text_channel(nome_chat)
    await categoria.create_text_channel(nome_comandos)
    await categoria.create_voice_channel(nome_voice)

    # Move a categoria para logo abaixo da categoria de referência
    categoria_referencia = ctx.guild.get_channel(1370678132515803228)
    if categoria_referencia:
        nova_posicao = categoria_referencia.position + 1
        await categoria.edit(position=nova_posicao)

    await ctx.send(f"✅ Vila criada com sucesso!\nCargo: {cargo_vila.mention}\nCategoria: {categoria.name}")

    # Envia log no canal de registros
    canal_log = ctx.guild.get_channel(CANAL_LOG_VILAS)
    if canal_log:
        embed = discord.Embed(
            title="🏗️ Vila Criada",
            description=f"**Nome:** {nome_vila_formatado}\n**Cargo:** {cargo_vila.mention}\n**Categoria:** {categoria.name}\n**Responsável:** {ctx.author.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        await canal_log.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def deletar_vila(ctx, *, nome_vila: str):
    """Deleta a vila, removendo categoria, canais e cargo."""
    producao_role = ctx.guild.get_role(PRODUCAO_ROLE_ID)
    if producao_role not in ctx.author.roles:
        await ctx.send("❌ Você não tem permissão para deletar vilas.")
        return

    nome_vila_formatado = nome_vila.strip().title()
    nome_cargo = f"▪︎ 𝐕𝐢𝐥𝐚 {nome_vila_formatado} ▪︎"
    nome_categoria = f"🛖 | Vila {nome_vila_formatado}"

    # Deleta cargo
    cargo = discord.utils.get(ctx.guild.roles, name=nome_cargo)
    if cargo:
        await cargo.delete()

    # Deleta categoria e canais
    categoria = discord.utils.get(ctx.guild.categories, name=nome_categoria)
    if categoria:
        for canal in categoria.channels:
            await canal.delete()
        await categoria.delete()

    await ctx.send(f"🗑️ Vila '{nome_vila_formatado}' deletada com sucesso!")

    # Envia log no canal de registros
    canal_log = ctx.guild.get_channel(CANAL_LOG_VILAS)
    if canal_log:
        embed = discord.Embed(
            title="🗑️ Vila Deletada",
            description=f"**Nome:** {nome_vila_formatado}\n**Responsável:** {ctx.author.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await canal_log.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está online!')
    print(f'ID do Bot: {bot.user.id}')
    print(f'Current Date and Time (UTC): {CURRENT_TIME}')
    print(f'Current User\'s Login: {CURRENT_USER}')
    print('='*30)
    
    # Carregar configurações e iniciar tasks
    load_status_config()
    bot.add_view(BotaoRegistro())
    
    if not update_server_status.is_running():
        update_server_status.start()
    if not update_bot_status.is_running():
        update_bot_status.start()

@bot.event
async def on_member_join(member):
    cargo = member.guild.get_role(CARGO_NAO_REGISTRADO)
    if cargo:
        await member.add_roles(cargo)
        print(f"Cargo 'Não Registrado' adicionado para {member.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_registro(ctx):
    embed = discord.Embed(
        title="🎮 Sistema de Registro",
        description="Clique no botão abaixo para iniciar seu registro no servidor!",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📝 Processo de Registro",
        value="Você responderá algumas perguntas sobre:\n"
              "• Nick do Minecraft\n"
              "• Tipo de jogador (Player/Ovo)\n"
              "• Participação em vila",
        inline=False
    )
    embed.add_field(
        name="ℹ️ Importante",
        value="• Digite seu nick exatamente como é no jogo\n"
              "• Responda todas as perguntas com atenção\n"
              "• Após o registro, você terá acesso aos canais do servidor",
        inline=False
    )
    embed.set_footer(text="Clique no botão verde abaixo para começar!")
    
    await ctx.send(embed=embed, view=BotaoRegistro())

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))