
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime
from fpdf import FPDF
from pdfrw import PdfReader, PdfWriter, PageMerge
import os
import configparser
import ast
import sys
import json
import re


def resource_path(relative):
    """PyInstaller 兼容字体路径"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)
LiShu_path = resource_path("fonts/simli.ttf")
KaiTi_path = resource_path("fonts/simkai.ttf")
mahjong_path = resource_path("fonts/S-MAHJONG.TTF")
mahjong_separator_path = resource_path("fonts/ma______.ttf")
times_new_roman_path = resource_path("fonts/times.ttf")

pdfmetrics.registerFont(TTFont("LiShu-Regular", LiShu_path))
pdfmetrics.registerFont(TTFont("KaiTi-Regular", KaiTi_path))
pdfmetrics.registerFont(TTFont("Mahjong-Regular", mahjong_path))
pdfmetrics.registerFont(TTFont("MahjongSeparator-Regular", mahjong_separator_path))
pdfmetrics.registerFont(TTFont("TimesNewRoman-Regular", times_new_roman_path))
# 注册字体
"""
try:
    # 尝试从fonts子目录加载字体
    #pdfmetrics.registerFont(TTFont('KaiTi', 'fonts/simkai.ttf'))
    #pdfmetrics.registerFont(TTFont('LiShu', 'fonts/simli.ttf'))
    pdfmetrics.registerFont(TTFont('Mahjong', 'fonts/S-MAHJONG.TTF'))
    pdfmetrics.registerFont(TTFont('MahjongSeparator', 'fonts/ma______.ttf'))
    pdfmetrics.registerFont(TTFont('TimesNewRoman', 'fonts/times.ttf'))
except:
    print("警告: 未找到所需字体，使用默认字体")
"""
# 自定义样式
styles = getSampleStyleSheet()
body_style = styles['BodyText']
title_style = ParagraphStyle(
    name='TitleStyle',
    parent=styles['Title'],
    fontName='LiShu-Regular',
    fontSize=24,
    textColor=colors.darkblue,
    alignment=1
)

date_style = ParagraphStyle(
    name='DateStyle',
    parent=styles['Title'],
    fontName='LiShu-Regular',
    fontSize=14,
    textColor=colors.darkblue,
    alignment=1
)

header_style = ParagraphStyle(
    'HeaderStyle',
    parent=styles['Heading2'],
    fontName='KaiTi-Regular',
    fontSize=14,
    textColor=colors.black,
    alignment=1
)

player_style = ParagraphStyle(
    'PlayerStyle',
    parent=styles['BodyText'],
    fontName='KaiTi-Regular',
    fontSize=16,
    leading=28,
    firstLineIndent=0
)

player_style_small = ParagraphStyle(
    'PlayerStyleSmall',
    parent=styles['BodyText'],
    fontName='KaiTi-Regular',
    fontSize=16,
    leading=20
)

player_name_style = ParagraphStyle(
    'PlayerNameStyle',
    parent=player_style,
    alignment=1,
    textColor=colors.darkblue
)

player_position_style = ParagraphStyle(
    'PlayerPositionStyle',
    parent=player_name_style,
    fontSize=14,
    textColor=colors.black
)

score_style = ParagraphStyle(
    'ScoreStyle',
    parent=player_name_style,
    alignment=2,
    fontSize=10,
    leading=20
)

# 麻将字符映射表
MAHJONG_MAPPING = {
    '1m': 'q', '2m': 'w', '3m': 'e', '4m': 'r', '5m': 't', '6m': 'y', '7m': 'u', '8m': 'i', '9m': 'o',
    '1p': 'a', '2p': 's', '3p': 'd', '4p': 'f', '5p': 'g', '6p': 'h', '7p': 'j', '8p': 'k', '9p': 'l',
    '1s': 'z', '2s': 'x', '3s': 'c', '4s': 'v', '5s': 'b', '6s': 'n', '7s': 'm', '8s': ',', '9s': '.',
    '1z': '1', '2z': '2', '3z': '3', '4z': '4', '5z': '5', '6z': '6', '7z': '7', '0m': 'p', '0p': ';', '0s': '/',
    't1m': 'Q', 't2m': 'W', 't3m': 'E', 't4m': 'R', 't5m': 'T', 't6m': 'Y', 't7m': 'U', 't8m': 'I', 't9m': 'O',
    't1p': 'A', 't2p': 'S', 't3p': 'D', 't4p': 'F', 't5p': 'G', 't6p': 'H', 't7p': 'J', 't8p': 'K', 't9p': 'L',
    't1s': 'Z', 't2s': 'X', 't3s': 'C', 't4s': 'V', 't5s': 'B', 't6s': 'N', 't7s': 'M', 't8s': '<', 't9s': '>',
    't1z': '!', 't2z': '@', 't3z': '#', 't4z': '$', 't5z': '%', 't6z': '^', 't7z': '&', 't0m': 'P', 't0p': ':', 't0s': '?',
    'N': '-', 'd':'0', 'r':'/', 'b':'-', 'c': 'P', 'p': 'p', '`': ']', 'R':'[', 'M':'`', 'C':'{', 'k':';', 'm':':', 'a':'+',
    'j':'*',
}

class MahjongGame:
    def __init__(self, title, date, round_info, deposits, dora1, dora2, dora3, dora4, dora5,uradora1,uradora2,uradora3,uradora4,uradora5, players):
        self.title = title
        self.date = date
        self.round_info = round_info
        self.deposits = deposits
        self.dora1= dora1
        self.dora2= dora2
        self.dora3= dora3
        self.dora4= dora4
        self.dora5= dora5
        self.uradora1 = uradora1
        self.uradora2 = uradora2
        self.uradora3 = uradora3
        self.uradora4 = uradora4
        self.uradora5 = uradora5
        self.players = players
        self.annotations = []  # 存储标注信息
        
        # 每个玩家行的起始位置 (x, y) 毫米单位
        self.player_start_positions = [
            (55.3, 51.3),   # 东家起始位置 (x, y)
            (55.3, 108.3),  # 南家起始位置
            (55.3, 165.2),  # 西家起始位置
            (55.3, 222.3)   # 北家起始位置
        ]
        
        # 每个玩家内部的行高 (毫米)
        self.player_row_heights = [12, 12, 12, 12]  # 四行的高度
    
    def create_base_pdf(self, filename):
        """使用ReportLab创建基础PDF"""
        doc = SimpleDocTemplate(filename, pagesize=A4, 
                                leftMargin=1.5*cm, rightMargin=1.5*cm,
                                topMargin=1*cm, bottomMargin=1*cm)
        
        # 主表格数据
        table_data = []
        
        # 第一行：标题
        title_text = f"<b>{self.title}</b><font name='KaiTi-Regular' size='12' color='black'>{self.date}</font>"
        table_data.append([Paragraph(title_text, title_style)])

        # 第二行：公告信息
        dora_text = f"宝牌 {self.convert_to_mahjong(self.dora1)}{self.convert_to_mahjong(self.dora2)}{self.convert_to_mahjong(self.dora3)}{self.convert_to_mahjong(self.dora4)}{self.convert_to_mahjong(self.dora5)}  里宝 {self.convert_to_mahjong(self.uradora1)}{self.convert_to_mahjong(self.uradora2)}{self.convert_to_mahjong(self.uradora3)}{self.convert_to_mahjong(self.uradora4)}{self.convert_to_mahjong(self.uradora5)}"
        info_text = f"{self.round_info} | {self.deposits} | {dora_text}"
        table_data.append([Paragraph(info_text, header_style)])
        
        # 玩家行
        for player in self.players:
            # 左侧：位置和姓名
            position_cell = self.create_position_cell(player)
            
            # 点数信息（放在右上角）
            score_cell = Paragraph(self.format_score(player), score_style)
            
            # 牌谱详情（四行）
            hand_details = [
                Paragraph(f"<font name='MahjongSeparator-Regular' size='30' color='black'>-</font>{self.format_tiles(player['starting_hand'])}", player_style),
                Paragraph(f"<font name='MahjongSeparator-Regular' size='30' color='black'>`</font>{self.format_tiles(player['draws'])}", player_style),
                Paragraph(f"<font name='MahjongSeparator-Regular' size='30' color='black'>^</font>{self.format_discards(player['discards'], player['riichi_index'])}", player_style),
                Paragraph(f"<font name='MahjongSeparator-Regular' size='30' color='black'>~</font>{self.format_final_hand(player)}", player_style)
            ]
            
            # 创建牌谱详情表格（四行一列）
            details_table = Table([[detail] for detail in hand_details], colWidths=[15.5*cm],)
            details_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('PADDING', (0,0), (-1,-1), (0, 0)),
                ('BOX', (0,0), (-1,-1), 0, colors.transparent)
            ]))
            
            # 创建右上角点数区域和牌谱详情区域的组合
            combined_table = Table([
                [score_cell, None],  # 第一行：点数（右上角）和空单元格
                [details_table, None]  # 第二行：牌谱详情（跨两列）
            ], colWidths=[15.3*cm, 15.0*cm], rowHeights=[0.00001*cm, 4.99999*cm])
            
            combined_table.setStyle(TableStyle([
                ('SPAN', (1,0), (1,1)),  # 牌谱详情跨两列
                ('VALIGN', (0,0), (1,1), 'TOP'),
                ('ALIGN', (0,0), (0,0), 'RIGHT'),
                ('BACKGROUND', (0,0), (0,0), colors.white),
                ('BOX', (0,0), (-1,-1), 0, colors.transparent),
                ('ROWGAP', (0,0), (1,0), 0)  # 设置第一行和第二行的行间距为 10 磅
            ]))
            
            # 玩家行：左侧位置 + 右侧组合
            player_row = [position_cell, combined_table]
            table_data.append(player_row)
        
        # 创建主表格（6行2列）
        main_table = Table(table_data, 
                          colWidths=[3*cm, 15.5*cm],
                          rowHeights=[1.5*cm, 1.2*cm] + [5.7*cm]*4)  # 标题、公告、4个玩家行
        
        # 设置表格样式
        table_style = TableStyle([
            # 标题行
            ('BACKGROUND', (0,0), (1,0), colors.lightgrey),
            ('ALIGN', (0,0), (1,0), 'CENTER'),
            ('VALIGN', (0,0), (1,0), 'MIDDLE'),
            ('SPAN', (0,0), (1,0)),  # 合并单元格
            
            # 公告行
            ('BACKGROUND', (0,1), (1,1), colors.white),
            ('TEXTCOLOR', (0,1), (1,1), colors.black),
            ('ALIGN', (0,1), (1,1), 'CENTER'),
            ('VALIGN', (0,1), (1,1), 'TOP'),
            ('SPAN', (0,1), (1,1)),  # 合并单元格
            
            # 玩家位置单元格
            ('BACKGROUND', (0,2), (0,5), colors.beige),
            ('VALIGN', (0,2), (0,5), 'MIDDLE'),
            ('ALIGN', (0,2), (0,5), 'CENTER'),
            
            # 牌谱详情单元格
            ('VALIGN', (1,2), (1,5), 'TOP'),
            
            # 全局边框
            ('GRID', (0,0), (1,5), 1, colors.black),
        ])
        
        main_table.setStyle(table_style)
        
        # 生成PDF
        doc.build([main_table])
    
    def create_position_cell(self, player):
        """创建左侧玩家位置和姓名的单元格"""
        position_text = f"<b>{player['position']}</b>"
        name_text = player['name']
        content = f"{position_text}<br/>{name_text}"
        return Paragraph(content, player_position_style)

    def convert_to_mahjong(self, tile_str, name='Mahjong-Regular', color=None ):
        """将麻将牌转换为麻将字体对应的字符"""
        # ① 处理 None
        if tile_str is None:
            return ""   # 或者返回一个空白占位符
        # 处理加杠牌（以"tt"开头）
        if tile_str.startswith('tt'):
            base_tile = tile_str[2:]  # 去掉"tt"前缀
            # 返回加杠牌（显示为横置牌）
            return f"<font name='{name}' size='24'>{MAHJONG_MAPPING.get('t' + base_tile, base_tile)} </font>"
        # color='{color}'
        # 检查是否有标注前缀（兼容 rd/rN/r60 等特殊牌码）
        if tile_str and tile_str[0] in ['r', 'c', 'p', 'k','m','a','j','`','C','R','M'] and len(tile_str) >= 2:
            mark_char = tile_str[0]
            tile_code = tile_str[1:]
            # 若剩余部分是纯数字（如 "60"→d, "16"→6m），先转换为麻将牌码
            if tile_code.isdigit():
                tile_code = convert_number_to_tile(int(tile_code))
            # 返回麻将牌（标注将在后续步骤添加）
            return f"<font name='{name}' size='24'>{MAHJONG_MAPPING.get(tile_code, tile_code)} </font>"
        
        # 特殊处理空牌
        if tile_str == 'N':
            return f"<font name='Mahjong-Regular' size='24' color='white'>{MAHJONG_MAPPING.get(tile_str, tile_str)} </font>"
        #
        # 特殊处理分隔符
        #if tile_str == 'd':
        #    return f"<font name='Mahjong' size='24' color='black'>{MAHJONG_MAPPING.get(tile_str, tile_str)}</font>"
        
        # 处理空格分隔的多个牌
        if ' ' in tile_str:
            tiles = tile_str.split()
            return ' '.join([self.convert_to_mahjong(tile) for tile in tiles])
        
        # 默认处理
        return f"<font name='{name}' size='24'>{MAHJONG_MAPPING.get(tile_str, tile_str)} </font>"

    def format_tiles(self, tiles):
        """格式化牌组显示为麻将字体（支持标注）"""
        return "".join([self.convert_to_mahjong(tile) for tile in tiles])
    
    def format_discards(self, discards, riichi_index):
        """格式化舍牌序列，立直牌加*标记（支持标注）"""
        formatted = []
        
        for i, tile in enumerate(discards):
            if i == riichi_index:
                formatted.append(f"{self.convert_to_mahjong(tile)}")
            else:
                formatted.append(self.convert_to_mahjong(tile))
        return "".join(formatted)
    
    def format_final_hand(self, player):
        """格式化最终牌型：手牌 + 副露 + 胡牌张（支持加杠）"""
        hand_tiles = self.format_tiles(player['final_hand'])
        
        # 副露部分
        calls = []
        if player['calls']:
            for call in player['calls']:
                # 处理加杠组（"tt8s"作为加杠牌）
                if call['tiles'] and call['tiles'][0].startswith('tt'):
                    # 加杠组：加杠牌 + 2个普通牌
                    mahjong_tiles = [
                        self.convert_to_mahjong(call['tiles'][0]),  # 加杠牌
                        self.convert_to_mahjong(call['tiles'][1]),  # 普通牌
                        self.convert_to_mahjong(call['tiles'][2])   # 普通牌
                    ]
                    calls.append("".join(mahjong_tiles))
                else:
                    # 普通副露组
                    mahjong_tiles = [self.convert_to_mahjong(tile) for tile in call['tiles']]
                    calls.append("".join(mahjong_tiles))
        
        # 组合
        result = hand_tiles
        if player['is_winner']:
            result += f"&nbsp;{self.convert_to_mahjong(player['winning_tile'])}"
        if calls:
            result += "&nbsp;" + " &nbsp;".join(calls)
        
        return result
    
    def format_score(self, player):
        """格式化点数显示（保持不变）"""
        score_before = player['score_before']
        score_after = player['score_after']
        point_change = score_after - score_before
        
        score_text = [f"{score_before}"]
        if point_change != 0:
            color = 'green' if point_change > 0 else 'red'
            sign = '+' if point_change > 0 else ''
            score_text.append(f"<font color='{color}'>{sign}{point_change}</font>")
        else:
            score_text.append("")
        score_text.append(f"{score_after}")
        
        return "<br/>".join(score_text)
    
    def create_pdf_with_annotations(self, filename):
        """创建带有标注的PDF（结合ReportLab和fpdf2/pdfrw）"""
        # 第一步：创建基础PDF（不带标注）
        base_pdf_path = "temp_base.pdf"
        self.create_base_pdf(base_pdf_path)
        
        # 第二步：使用fpdf2添加标注
        annotations_pdf_path = "temp_annotations.pdf"
        self.create_annotations_pdf(annotations_pdf_path)
        
        # 第三步：合并基础PDF和标注PDF
        self.merge_pdfs(base_pdf_path, annotations_pdf_path, filename)
        
        # 删除临时文件
        if os.path.exists(base_pdf_path):
            os.remove(base_pdf_path)
        if os.path.exists(annotations_pdf_path):
            os.remove(annotations_pdf_path)
    
    def create_annotations_pdf(self, output_pdf_path):
        """使用fpdf2创建只包含标注的PDF"""
        # 创建fpdf2对象
        pdf = FPDF()
        pdf.add_page()
        
        def register_fpdf_fonts(pdf):
            """为 FPDF 注册自定义字体（兼容 exe）"""
            sep_path = resource_path("fonts/ma______.ttf")
            sep_path1 = resource_path("fonts/S-MAHJONG.ttf")
            sep_path2 = resource_path("fonts/simkai.TTF")
            if not os.path.exists(sep_path):
                print("字体不存在：", sep_path)
            if not os.path.exists(sep_path1):
                print("字体不存在：", sep_path1)
            if not os.path.exists(sep_path2):
                print("字体不存在：", sep_path2)

            try:
                pdf.add_font("MahjongSeparator", "", sep_path, uni=True)
                pdf.add_font("Mahjong", "", sep_path1, uni=True)
                pdf.add_font("KaiTi", "", sep_path2, uni=True)
            except Exception as e:
                print("字体注册失败：", e)

        register_fpdf_fonts(pdf)
       
        # 为每个玩家添加标注
        for player_idx, player in enumerate(self.players):
            # 获取当前玩家的起始位置
            start_x, start_y = self.player_start_positions[player_idx]
            
            # 获取当前玩家的行高
            row_height = self.player_row_heights[player_idx]
            
            # 为当前玩家的四行添加标注
            self.add_player_annotations(pdf, player, start_x, start_y, row_height)
        
        # 保存结果
        pdf.output(output_pdf_path)
        #print(f"标注PDF已生成: {output_pdf_path}")
    
    def add_player_annotations(self, pdf, player, start_x, start_y, row_height):
        """为单个玩家的四行添加标注，并处理胡牌张标注"""
        # 起始手牌行
        y = start_y
        self.add_row_annotations(pdf, player['starting_hand'], start_x, y)
        
        # 摸牌行
        y += row_height
        self.add_row_annotations(pdf, player['draws'], start_x, y)
        
        # 舍牌行
        y += row_height
        self.add_row_annotations(pdf, player['discards'], start_x, y)
        
        # 最终手牌行
        y_final = start_y + 3 * row_height
        self.add_row_annotations(pdf, player['final_hand'], start_x, y_final)

        # 胡牌张的标注（如果玩家是胡牌者）
        if player['is_winner']:
            # 计算胡牌张的位置：在最终手牌行之后
            # 手牌数量
            final_hand_count = len(player['final_hand'])
            # 计算副露中的牌数和横置牌数量
            calls_tiles_count = 0
            tilted_tiles_count = 0  # 横置牌的数量
            for call in player['calls']:
                # 计算横置牌（以"t"开头的牌）
                for tile in call['tiles']:
                    calls_tiles_count += 1
                    if tile.startswith('t') or tile.startswith('tt'):
                        tilted_tiles_count += 1
        
            # 副露之间的空格数（每个副露之间2个空格）
            spaces_count = 1 * len(player['calls']) +1  # 副露组之间的空格
            
            # 胡牌张的位置 = 手牌数 + 副露牌数 + 空格数
            winning_tile_pos = final_hand_count   #calls_tiles_count + spaces_count
            x_winning = start_x + winning_tile_pos * 5.63 + 2.53  # tilted_tiles_count * 1.87 - spaces_count*2.53
            # 添加胡牌张标注
            self.add_tile_annotation(pdf, player['winning_tile'], x_winning, y_final)
        
        # 添加加杠标注
        self.add_kong_annotations(pdf, player, start_x, y_final)
    
    def add_kong_annotations(self, pdf, player, start_x, y):
        """添加加杠标注"""
        # 计算最终手牌行的起始位置
        x = start_x
        hand_offset = len(player['final_hand']) * 5.63
        
        # 遍历所有副露
        for call in player['calls']:
            tiles = call['tiles']
            # 计算当前副露组的起始位置：手牌结束位置 + 组前空格
            call_start_x = x + hand_offset + 2.82  # 10.6mm = 2个牌位的空格       
            # 初始化组内位置
            tile_x = call_start_x 
            if player["is_winner"]:
                tile_x += 8.36   
            # 遍历副露组内的每张牌
            for tile in tiles:       
                # 检查是否是加杠牌（以"tt"开头）
                if tile.startswith('tt'):
                    # 提取加杠牌信息（例如："tt8s"")
                    kong_tile = tile[1:]
                    
                    Tx = call.get("Tx", 0)
                    #print(Tx)
                    #print(kong_tile)
                    if Tx == 1:
                        # 红普通切换
                        if kong_tile[1] == '5':   # 普通五 → 红五
                            kong_tile = kong_tile[0] + '0' + kong_tile[2:]
                        elif kong_tile[1] == '0': # 红五 → 普通五
                            kong_tile = kong_tile[0] + '5' + kong_tile[2:]
                    kong_tile_mapping = MAHJONG_MAPPING[kong_tile]
                    #print(kong_tile)
                    # 添加加杠标注（在横置牌上方）
                    pdf.set_font("Mahjong", size=24)
                    pdf.set_text_color(0, 0, 0)  # 黑色
                    pdf.text(tile_x + 1.48, y - 3.8, kong_tile_mapping)  # 加杠符号
            
                # 计算当前牌的宽度并移动到下一张牌位置
                tile_width = 7.50 if tile.startswith(('t', 'tt')) else 5.63
                tile_x += tile_width
            # 计算副露组宽度（加杠组占3个位置：横置牌+2个竖直牌）
            call_width = 0
            for tile in tiles:
                if tile.startswith('t') or tile.startswith('tt'):
                    # 横置牌或加杠横置牌
                    call_width += 7.50
                else:
                    # 正常牌
                    call_width += 5.63
            
            # 移动到下一个副露组位置
            hand_offset += call_width + 2.82  # 加上组间空格

    def add_tile_annotation(self, pdf, tile_str, x, y):
        """为单个麻将牌添加标注"""
        # 检查是否有标注前缀（兼容 rd/rN/r60 等特殊牌码）
        if tile_str and tile_str[0] in ['r', 'c', 'p', 'k','m','a','j','`','C','R','M'] and len(tile_str) >= 2:
            mark_char = MAHJONG_MAPPING.get(tile_str[0], tile_str[0])

            # 添加标注
            pdf.set_font("MahjongSeparator", size=18)
            pdf.set_text_color(0, 0, 0)  # 黑色
            # 计算标注位置（牌的中心上方）
            pdf.text(x + 1.8, y - 5, mark_char) 

    def add_row_annotations(self, pdf, tiles, start_x, y):
        """为一行麻将牌添加标注"""
        x = start_x
        for tile in tiles:
            # 检查是否有标注前缀（兼容 rd/rN/r60 等特殊牌码）
            if tile and tile[0] in ['r', 'c', 'p', 'k','m','a','j','`','C','R','M'] and len(tile) >= 2:
                mark_char = MAHJONG_MAPPING.get(tile[0], tile[0])
                # 添加标注
                pdf.set_font("MahjongSeparator", size=18)
                pdf.set_text_color(0, 0, 0)  # 红色标注
                
                # 计算标注位置（牌的中心上方）
                pdf.text(x + 1.8, y - 5, mark_char)
            
            # 移动到下一个牌的位置（假设每个牌宽度为10毫米）
            x += 5.63
    
    def merge_pdfs(self, base_pdf_path, annotations_pdf_path, output_pdf_path):
        """使用pdfrw合并基础PDF和标注PDF"""
        # 读取基础PDF
        base_pdf = PdfReader(base_pdf_path)
        
        # 读取标注PDF
        annotations_pdf = PdfReader(annotations_pdf_path)
        
        # 确保两个PDF都有页面
        if not base_pdf.pages or not annotations_pdf.pages:
            print("错误: 无法读取PDF页面")
            return
        
        # 获取基础PDF的第一页
        base_page = base_pdf.pages[0]
        
        # 获取标注PDF的第一页
        annotations_page = annotations_pdf.pages[0]
        
        # 创建PageMerge对象来合并页面
        merger = PageMerge(base_page)
        merger.add(annotations_page).render()
        
        # 写入最终PDF
        writer = PdfWriter()
        writer.addpage(base_page)
        writer.write(output_pdf_path)

def parse_tile_string(tile_str):
    """增强版牌谱解析函数，支持多种输入格式"""
    # 处理空值
    if not tile_str or tile_str.lower() in ['[]', 'none', 'null']:
        return []
    
    # 尝试直接解析为列表
    try:
        return ast.literal_eval(tile_str)
    except:
        pass
    
    # 处理没有引号的情况 (e.g. [1m, 2m, 3m])
    if tile_str.startswith('[') and tile_str.endswith(']'):
        # 移除方括号并分割
        inner = tile_str[1:-1].strip()
        if not inner:
            return []
        
        # 分割元素并清理
        tiles = []
        for item in inner.split(','):
            item = item.strip()
            # 移除可能的引号
            if item.startswith(('"', "'")) and item.endswith(('"', "'")):
                item = item[1:-1]
            tiles.append(item)
        return tiles
    
    # 处理空格分隔的字符串 (e.g. "1m 2m 3m")
    return tile_str.split()

def convert_number_to_tile(number):
    """将数字转换为麻将牌字符串"""
    if number == 0:
        return 'N'
    elif number == 60:
        return 'd'
    elif 11 <= number <= 19:
        return f"{number-10}m"
    elif 21 <= number <= 29:
        return f"{number-20}p"
    elif 31 <= number <= 39:
        return f"{number-30}s"
    elif 41 <= number <= 47:
        return f"{number-40}z"
    elif number == 51:
        return "0m"
    elif number == 52:
        return "0p"
    elif number == 53:
        return "0s"
    else:
        return str(number)

def get_dora_tile(indicator):
    """根据指示牌获取宝牌"""
    if indicator == 0:
        return ""
    
    tile = convert_number_to_tile(indicator)
    
    if tile.endswith('m') or tile.endswith('p') or tile.endswith('s'):
        suit = tile[-1]
        value = int(tile[:-1])
        
        # 处理红宝牌
        if value == 0:  # 红5
            return f"6{suit}"
        elif value == 9:  # 9 -> 1
            return f"1{suit}"
        else:
            return f"{value+1}{suit}"
    
    elif tile.endswith('z'):
        value = int(tile[:-1])
        if 1 <= value <= 4:  # 风牌
            return f"{(value % 4) + 1}z"
        elif 5 <= value <= 7:  # 三元牌
            return f"{5 + ((value - 4) % 3)}z"
    
    return tile

import re
from collections import defaultdict

def _tokenize_call_str(s):
    """将 call_str 拆成 tokens ['25','p','25','25'] 形式"""
    if s is None:
        return []
    return re.findall(r'\d{2}|[a-zA-Z]', s)

def _detect_source(tokens):
    """
    根据 token 位置判断来源类型：
      - token index == 1 -> 'across' (对家)
      - token index >= 2 -> 'left' (下家)
      - else -> None
    """
    for i, tk in enumerate(tokens):
        if tk in ('p', 'm'):
            if i == 1: return 'across'
            if i >= 2: return 'left'
    return None

def _infer_event_type(call):
    """
    事件 call 可以包含字段 'type' (preferred).
    如果没有, 尝试根据 call_str 推断:
      - contains 'a' at rem start -> 'ankan' (暗杠)
      - contains 'k' -> 'added_kong' (加杠/抢杠)
      - if tokens contain 'm' and number of numeric groups >=4 -> 'open_kong' (明杠)
      - else 'pon' for p / 'chi' for c (both treated like pon for skipping)
    Return one of: 'pon'|'open_kong'|'added_kong'|'ankan'
    """
    if 'type' in call and call['type']:
        return call['type']

    s = call.get('call_str','')
    rem = call.get('remaining','')
    # check remaining 'a...' (ankan)
    if isinstance(rem, str) and rem.find('a')>=0:
        return 'ankan'
    # check call_str for 'k' (added kong)
    if 'k' in s or (isinstance(rem,str) and rem.find('k')>=0):
        return 'added_kong'
    tokens = _tokenize_call_str(s)
    # open kong heuristic: many numeric groups and 'm' present
    num_digits = sum(1 for tk in tokens if re.fullmatch(r'\d{2}', tk))
    if 'm' in tokens and num_digits >= 4:
        return 'open_kong'
    # default: pon/chi
    if 'p' in tokens or 'c' in tokens or 't' in s:
        return 'pon'
    return 'pon'

def insert_skips_advanced(all_draws, all_discards, all_calls):
    """
    all_draws: [draws_p0, draws_p1, draws_p2, draws_p3]  each is list
    all_discards: similar
    all_calls: list of dicts, each must contain:
        {
          "player": X (0..3),
          "index": i (round index for that player),
          "call_str": original string (e.g. "25p2525") OR "remaining": "p5s"
          optional: "type": one of 'pon','open_kong','added_kong','ankan'
        }
    The function mutates all_draws / all_discards in-place by inserting 'N' at computed positions.
    """

    # 1) collect all insert targets in original timeline coordinates (before any insert)
    # map (player, round_index) -> count of Ns to insert
    inserts = defaultdict(int)

    # helper to map global pos -> (player, round_idx)
    def pos_to_player_round(pos):
        player = pos % 4
        round_idx = pos // 4
        return player, round_idx
    #print(all_calls)
    # process each call, compute interval(s) in global pos coordinates (based on original indices)
    all_calls.sort(key=lambda x: (x.get("index"),x.get("player")))
    for call in all_calls:
        X = call.get("player")
        i = call.get("index")
        #print(X,i)
        if X is None or i is None:
            continue
        s = call.get("call_str", "")
        rem = call.get("remaining", "")
        
        offset = 0
        for (p,r) in inserts.keys():    
            if p == X and r < i:
                offset+=1
        i+=offset
       
        tokens = _tokenize_call_str(s)
        source = _detect_source(tokens)
        # fallback: if no call_str, try remaining
        #if source is None and isinstance(rem, str) and len(rem) >= 2 and rem[0] in ('p','m'):
            # remaining like 'p5s' -> treat as p at position 1 => across
            # but better tokenizing: 'p5s' -> tokens ['p','5s'] -> p at pos0 => ambiguous.
            # default to across if ambiguous
            #ource = 'across'

        event_type = _infer_event_type(call)

        self_pos = i * 4 + X  # global pos for this player's round i

        # determine start_pos for primary skip (for pon / open_kong / added_kong, etc.)
        # If call originates from a source player (down or across), compute source_pos accordingly
        if source == 'left':
            source_player = (X + 1) % 4  # down/left player (player who gave tile)
            if source_player<X:
                start_pos = i * 4 + source_player
                end_pos = self_pos
            else: 
                start_pos = (i-1) * 4 + source_player
                end_pos = self_pos
            # insert for positions in (start_pos, end_pos)
            #print("inserting N at", start_pos, "to", end_pos, "for", (X, i))
            for pos in range(start_pos + 1, end_pos):
                p, r = pos_to_player_round(pos)
                inserts[(p, r)] += 1
        elif source == 'across':
            source_player = (X + 2) % 4  # across/opposite
            if source_player<X:
                start_pos = i * 4 + source_player
                end_pos = self_pos
            else: 
                start_pos = (i-1) * 4 + source_player
                end_pos = self_pos
            for pos in range(start_pos + 1, end_pos):
                p, r = pos_to_player_round(pos)
                inserts[(p, r)] += 1
                #print("inserting N at", pos, "for", (p, r))
        else:
            # If source unknown but event_type indicates ankan/added_kong etc., handle below
            pass

        # Now handle special rules for kong types
        if event_type == 'open_kong':
            # first primary skip already done above (same as pon)
            # then second skip: from self (x+1) to self (x+2)
            start2 = i * 4 + X
            end2 = (i + 1) * 4 + X
            #print("inserting N at", start2, "to", end2, "for", (X, i+1))
            for pos in range(start2 + 1, end2):
                p, r = pos_to_player_round(pos)
                inserts[(p, r)] += 1
            # also ensure self.discard[x+1] gets an N (insert into self at round i+1)
            #inserts[(X, i + 1)] += 1  # this will cause an extra N at player's round i+1
        elif event_type in ('added_kong', 'ankan'):
            # for ankan and added kong: from self x to self x+1 skip three players
            startk = i * 4 + X
            endk = (i + 1) * 4 + X
            for pos in range(startk + 1, endk):
                p, r = pos_to_player_round(pos)
                inserts[(p, r)] += 1
    #print(inserts)
    """
    offset = [0,0,0,0]
    for call in all_calls:
        X = call.get("player")
        if X is None:
            continue
        print(list(inserts.keys()))
        rounds=list(inserts.keys())
        rounds.sort(key=lambda x: (x[0],x[1]))
        print(rounds)
        for (p,r) in rounds:
            if p == X and inserts[(p, r)] > 0:
                value=inserts[(p,r)]
                del inserts[(p,r)]
                r+=offset[X]
                inserts[(p,r)]=value
                offset[X]+=1
            else:
                pass
    print(inserts)
    """
    # 2) apply inserts to each player in ascending round order (so inserts indices remain valid)
    for p in range(4):
        # collect rounds for this player with counts
        rounds = [(r, inserts[(p, r)]) for (pp, r) in list(inserts.keys()) if pp == p and inserts[(p, r)] > 0]
        # sort by round index ascending
        rounds.sort(key=lambda x: x[0])
        offset = 0
        for r, cnt in rounds:
            # compute insertion index in current lists (after prior inserts for this player)
            idx = r #+ offset
            # ensure lists are long enough
            while len(all_draws[p]) < idx:
                all_draws[p].append(None)
            while len(all_discards[p]) < idx:
                all_discards[p].append(None)
            # insert cnt times at idx (pushes existing elements right)
            for _ in range(cnt):
                all_draws[p].insert(idx, "N")
                all_discards[p].insert(idx, "N")
                #print("before insert:", idx)
                #print("before offset:" ,offset)
                idx += 1
                offset += 1
                #print("after insert:", idx)
                #print("after offset:" ,offset)
    # done
    return

def rotate_indexes(index_list, round_num):
        """根据 round_num 旋转玩家编号列表"""
        return [ (idx - round_num) % 4 for idx in index_list ]

def rotate_player_data(round_num, names, initial_scores, player_data, final_scores,raw_winners, raw_losers):
    """根据局数旋转玩家数据"""
    # 计算旋转偏移量
    if round_num % 4 == 0:   #东1局或南1局
        offset = 0
    elif round_num % 4 == 1:  # 东2局或南2局
        offset = 1
    elif round_num % 4 == 2:  # 东3局或南3局
        offset = 2
    else:  
        offset = 3 # 东4局或南4局
    

    # 旋转名字数组
    rotated_names = names[offset:] + names[:offset]
    
    # 旋转初始分数
    rotated_initial_scores = initial_scores[offset:] + initial_scores[:offset]
    
    # 旋转最终分数变化
    rotated_final_scores = final_scores[offset:] + final_scores[:offset]
    
    # 旋转玩家数据
    rotated_player_data = player_data[offset:] + player_data[:offset]
    # 根据 round_num 将 winner / loser 座位也旋转
    rotated_winners_info = rotate_indexes(raw_winners, round_num)
    rotated_losers_info  = rotate_indexes(raw_losers, round_num)

    return rotated_names, rotated_initial_scores, rotated_final_scores, rotated_player_data,rotated_winners_info,rotated_losers_info
# ------------------ 新增：插入跳过 N 的函数 ------------------
def insert_skips_for_calls(all_draws, all_discards, all_calls):
    """
    all_draws: list of 4 lists (draws for each player) -- will be mutated in place
    all_discards: list of 4 lists (discards for each player) -- will be mutated in place
    all_calls: list of dicts: {"player": X, "index": i, "call_str": s}
    规则：
      - token 化 call_str 为 ['25','p','25','25'] 等；
      - 若 p/m 出现在 tokens 索引 i == 1 (第二项) -> 对家来源 -> skip 上家 (X-1)
      - 若 p/m 出现在 tokens 索引 i >= 2 -> 下家来源 -> skip 上家 (X-1) 与 对家 (X-2)
      - 在对应玩家 draws/discards 的位置 i 处插入字符串 'N' （insert，不替换）
    """
    import re

    for event in sorted(all_calls, key=lambda e: (e['index'], e['player'])):
        X = event['player']
        i = event['index']
        s = event['call_str']
        if not isinstance(s, str):
            continue

        # token 化：每两位数字为一项或字母为一项
        tokens = re.findall(r'\d{2}|[a-zA-Z]', s)
        if not tokens:
            continue

        # 找到第一个 p 或 m
        letter_pos = None
        for ti, tk in enumerate(tokens):
            if tk in ('p', 'm'):
                letter_pos = ti
                break
        if letter_pos is None:
            continue

        # 决定 skip_targets（使用 modulo 循环）
        skip_targets = set()
        if letter_pos == 1:
            # 对家来源 -> skip 上家
            skip_targets.add((X - 1) % 4)
        elif letter_pos >= 2:
            # 下家来源 -> skip 上家 & 对家
            skip_targets.add((X - 1) % 4)
            skip_targets.add((X - 2) % 4)
        else:
            # 其他情况不处理
            continue

        # 插入 'N'（insert，不替换）；若 index 超长度则 append
        for P in sorted(skip_targets):
            # ensure draws length
            if i <= len(all_draws[P]):
                all_draws[P].insert(i, "N")
            else:
                # 若 i 超出当前长度，直接补齐到 i 再插入
                while len(all_draws[P]) < i:
                    all_draws[P].append(None)
                all_draws[P].append("N")

            # 同步插入 discards
            if i <= len(all_discards[P]):
                all_discards[P].insert(i, "N")
            else:
                while len(all_discards[P]) < i:
                    all_discards[P].append(None)
                all_discards[P].append("N")
# ------------------ 新增结束 ------------------

# ---------- Helper: convert tile string back to number ----------
def convert_tile_to_number(tile_str):
    """
    将牌码（如 '8s','0m','t8s','tt8s','1z'）转换回原始数字编码。
    返回 int（例如 38, 51, 41 等），或 None（无法识别）。
    """
    if not tile_str:
        return None
    s = str(tile_str)
    # 去掉可能的前缀 't' 或 'tt'
    while s.startswith('t'):
        s = s[1:]
    # 现在 s 应为像 '8s' 或 '0m' 或 '1z'
    if len(s) < 2:
        return None
    val = s[:-1]
    suit = s[-1]
    # 红五编码
    if val == '0':
        if suit == 'm':
            return 51
        if suit == 'p':
            return 52
        if suit == 's':
            return 53
    # 数字牌
    try:
        n = int(val)
    except:
        return None
    if suit == 'm':
        return 10 + n  # 11..19
    if suit == 'p':
        return 20 + n  # 21..29
    if suit == 's':
        return 30 + n  # 31..39
    if suit == 'z':
        return 40 + n  # 41..47
    return None

# ---------- Helper: red-five equivalence ----------
def tile_number_equivalent(a, b):
    """判断两个数字编码是否等价（含红五对应关系）"""
    if a == b:
        return True
    red_map = {51:15, 52:25, 53:35, 15:51, 25:52, 35:53}
    return red_map.get(a) == b

# ---------- parse_call_string（完整替换） ----------
def parse_call_string(call_str, source=None):
    """
    解析副露字符串，返回 (parsed, remaining)
    对加杠：remaining = 'k' + <tile_string>
        例：'35k355335' -> remaining = 'k5s'
    """
    if call_str is None:
        return [], None

    s = str(call_str).strip().strip('"').strip("'")
    if s == "":
        return [], None

    # ---- 立直 ----
    if re.fullmatch(r"r\d{1,2}", s):
        num = int(s[1:])
        return None, f"r{convert_number_to_tile(num)}"

    # ---- 加杠：k + NN（两位数字）----
    if 'k' in s and source == 'discards':
        m = re.search(r'k(\d{2})', s)
        if m:
            num = int(m.group(1))
            tile = convert_number_to_tile(num)
            remaining = f'k{tile}'     # ★ 改成牌字符串
            return ("k-gang", num), remaining

    # ---- 普通副露/暗杠 ----
    parts = re.findall(r'[a-z]?\d{2}', s)
    if not parts:
        return [], None

    # ---- 暗杠：a 且在舍牌行 ----
    has_a = any(p[0] == 'a' for p in parts if p[0].isalpha())
    if has_a and source == 'discards':
        nums = [int(x[-2:]) for x in parts]

        reds = [n for n in nums if n in (51, 52, 53)]
        normals = [n for n in nums if n in (15, 25, 35)]

        if reds:
            red_tile = convert_number_to_tile(reds[0])
            normal_tile = convert_number_to_tile(normals[0]) if normals else red_tile
            if len(reds) >= 2:
                call_tiles = ['b', red_tile, red_tile, 'b']
            else:
                call_tiles = ['b', red_tile, normal_tile, 'b']
        else:
            base_tile = convert_number_to_tile(nums[0])
            call_tiles = ['b', base_tile, base_tile, 'b']

        remaining = "a" + convert_number_to_tile(nums[0])
        return call_tiles, remaining

    # ---- 吃/碰/明杠 ----
    call_tiles = []
    remaining_part = None

    for part in parts:
        if part[0].isalpha():  # 有字母的
            letter = part[0]
            num = int(part[1:])
            tile = convert_number_to_tile(num)

            if letter in ('m', 'a'):
                mapped = 'k'
            elif letter == 'k':
                mapped = 'j'
            else:
                mapped = letter

            remaining_part = mapped + tile
            call_tiles.append('t' + tile)
        else:
            num = int(part)
            tile = convert_number_to_tile(num)
            call_tiles.append(tile)

    return call_tiles, remaining_part

def tile_number_equivalent(a, b):
    """红五与普通五等价判断。"""
    if a == b:
        return True
    eq = {51: 15, 52: 25, 53: 35, 15: 51, 25: 52, 35: 53}
    return eq.get(a) == b


def process_player_calls(player_draws, player_discards):
    calls = []
    riichi_index = -1
    call_events = []

    # ---- Draws ----
    for idx, item in enumerate(player_draws):
        if isinstance(item, str):
            parsed, rem = parse_call_string(item, source='draws')

            if isinstance(rem, str):
                if rem.startswith("k") or rem.startswith("r") or re.match(r'^[a-z]', rem):
                    player_draws[idx] = rem

            if parsed is None:
                call_events.append(("riichi", "draws", idx, rem))
            elif isinstance(parsed, tuple) and parsed[0] == "k-gang":
                base_num = parsed[1]
                call_events.append(("k-gang", "draws", idx, base_num, rem))
            elif isinstance(parsed, list) and parsed:
                call_events.append(("call", "draws", idx, parsed, rem))

    # ---- Discards ----
    for idx, item in enumerate(player_discards):
        if isinstance(item, str):
            parsed, rem = parse_call_string(item, source='discards')

            if isinstance(rem, str):
                if rem.startswith("k") or rem.startswith("r") or re.match(r'^[a-z]', rem):
                    player_discards[idx] = rem

            if parsed is None:
                call_events.append(("riichi", "discards", idx, rem))
            elif isinstance(parsed, tuple) and parsed[0] == "k-gang":
                base_num = parsed[1]
                call_events.append(("k-gang", "discards", idx, base_num, rem))
            elif isinstance(parsed, list) and parsed:
                call_events.append(("call", "discards", idx, parsed, rem))

    # ---- 排序（执行顺序）----
    call_events.sort(key=lambda e: (e[2], 0 if e[1]=='draws' else 1))

    # ---- 执行事件 ----
    for ev in call_events:
        kind = ev[0]

        # ---- 立直 ----
        if kind == "riichi":
            _, source, idx, mark = ev
            if source == "draws":
                player_draws[idx] = mark
            else:
                player_discards[idx] = mark
                riichi_index = idx
            continue

        # ---- 吃/碰/明杠 ----
        if kind == "call":
            _, source, idx, tiles, rem = ev
            calls.append({"tiles": tiles,"remaining": rem})
            continue
            
        # ---- 加杠：修改原来的碰 ----
        if kind == "k-gang":
            _, source, idx, base_num, rem = ev

            # ---------------------------------------------------------
            # 1) 基础 tile：优先 rem（如 "k5s" → "5s"）
            # ---------------------------------------------------------
            if isinstance(rem, str) and rem.startswith("k"):
                base_tile_raw = rem[1:]        # remove leading "k"
            else:
                base_tile_raw = convert_number_to_tile(base_num)

            # ---------------------------------------------------------
            # 工具：清洗 tile 前缀 t/tt → 得到纯牌符号（例如 "t0s" → "0s"）
            # ---------------------------------------------------------
            def clean(tile):
                if not isinstance(tile, str):
                    return None
                s = tile
                while s.startswith('t'):
                    s = s[1:]
                return s

            # 判断是否红五 tile (0m/0p/0s)
            def is_red_tile_str(tile_str):
                ct = clean(tile_str)
                return ct and ct[0] == '0'

            # 取得花色（最后一位）
            def suit_of(tile_str):
                ct = clean(tile_str)
                return ct[-1] if ct else None

            # 从 remaining 中提取声明 tile，例如 "p5s" → "5s"
            def declared_from_remaining(rem):
                if isinstance(rem, str) and len(rem) >= 2:
                    return rem[1:]
                return None

            # ---------------------------------------------------------
            # 2) 找对应碰（依据 tile_number_equivalent 验证 base_num）
            # ---------------------------------------------------------
            for c in calls:
                tiles = c.get("tiles", [])
                if not tiles:
                    continue

                # sample_num 用来判断是否为对应的碰
                sample_real_tile = None
                for t in tiles:
                    if not (isinstance(t, str) and t.startswith('t')):
                        sample_real_tile = clean(t)
                        break
                if sample_real_tile is None:
                    sample_real_tile = clean(tiles[0])

                sample_num = convert_tile_to_number(sample_real_tile)
                if sample_num is None:
                    continue

                # 是否是此加杠真正要匹配的碰
                if not tile_number_equivalent(sample_num, base_num):
                    continue

                # ---------------------------------------------------------
                # 3) 找到碰之后，确定“声明 tile” sample_tile
                # 顺序：横置牌 > remaining > fallback
                # ---------------------------------------------------------
                declared_tile = None

                # (1) 横置牌
                for t2 in tiles:
                    if isinstance(t2, str) and t2.startswith('t'):
                        declared_tile = clean(t2)   # t5s → 5s
                        break

                # (2) remaining（p5s/p0s）
                if declared_tile is None and c.get("remaining"):
                    declared_tile = declared_from_remaining(c["remaining"])

                # (3) fallback：第一张 clean tile
                if declared_tile is None:
                    declared_tile = clean(tiles[0])

                # ---------------------------------------------------------
                # 4) 判断红五冲突 Tx
                # base_clean：加杠声明 tile
                # declared_tile：碰的声明 tile
                # ---------------------------------------------------------
                base_clean = clean(base_tile_raw)
                sample_clean = declared_tile

                Tx = 0
                if suit_of(base_clean) == suit_of(sample_clean):
                    if is_red_tile_str(base_clean) != is_red_tile_str(sample_clean):
                        Tx = 1

                # 存给 add_kong_annotations 使用
                c["Tx"] = Tx

                # ---------------------------------------------------------
                # 5) 决定 ttX 用哪个 tile
                # Tx = 1 → 使用 sample_clean（碰的 tile）
                # Tx = 0 → 使用 base_clean（k-gang tile）
                # ---------------------------------------------------------
                tile_for_tt = sample_clean if Tx == 1 else base_clean

                # ---------------------------------------------------------
                # 6) 替换第一个 tX → ttX
                # ---------------------------------------------------------
                for i2, t2 in enumerate(tiles):
                    if isinstance(t2, str) and t2.startswith('t'):
                        tiles[i2] = "tt" + tile_for_tt
                        break

                break  # 完成此加杠，退出循环

            continue



            
    # 最终视觉顺序反转
    calls.reverse()
    #print(calls)
    #print(call_events)
    return calls, riichi_index,call_events 

def parse_winner_and_scores(log_last):
    """
    log_last: log[-1] ；通常是多个数组 concatenated 例如：
        [4200,0,0,-4200],
        [0,3,0,"30符3飜3900点","断么九","ドラ(2飜)"],
        [0,2600,0,-2600],
        [1,3,1,"40符2飜2600点","対々和(2飜)"],
        ...
    或者为 ["流局"] / ["四槓散了"] 等

    返回结构：
      {
        "is_draw": True/False,
        "is_nagashi": True/False,
        "has_winning_tile": True/False,
        "winners": [...],
        "losers": [...],
        "score_delta": [p0,p1,p2,p3],
        "win_entries": [...]
      }
    """



    # ---------------------------------------------------------
    # 2. 不是流局 → 尝试解析多个荣和（包括一炮多响）
    #    log_last 应是多个 pair 形式：
    #       [Δ0,Δ1,Δ2,Δ3], [winner,loser,?, ...]
    # ---------------------------------------------------------
    idx = 0
    L = log_last
    N = len(L)

    winners = []
    losers = []
    score_delta = [0,0,0,0]
    win_entries = []
    has_winning_tile = True

    while idx < N:
        block = L[idx]

        # 点数变化块必定是 4 个数的数组
        if isinstance(block, list) and len(block)==4 and all(isinstance(x, int) for x in block):
            # 累积点数变化
            for p in range(4):
                score_delta[p] += block[p]
            idx += 1
            continue

        # 接下来应是胡牌信息块：[winner,loser,?, "xxx符yyy飜nn点", ...]
        if isinstance(block, list) and len(block)>=3 and isinstance(block[0], int) and isinstance(block[1], int):
            winner = block[0]
            loser  = block[1]

            winners.append(winner)
            losers.append(loser)
            win_entries.append(block)
            idx += 1
            continue

        # 其他未知内容 → 跳过
        idx += 1
    # ---------------------------------------------------------
    # 1. 先判断流局类
    # ---------------------------------------------------------
    DRAW_WORDS = ["流局", "九種九牌", "三家和了", "四風連打", "四槓散了", "四家立直"]

    if any(isinstance(x, str) and x in DRAW_WORDS for x in log_last):
        return {
            "is_draw": True,
            "is_nagashi": False,
            "has_winning_tile": False,
            "winners": [],
            "losers": [],
            "score_delta": score_delta,
            "win_entries": []
        }
    # ---------------------------------------------------------
    # 3. 流し満貫（nagashi mangan）判定：
    #    特点：虽然在 log_last 有 winner/loser 数字，但它是无胡牌张的特殊役。
    #    你的系统中：若 block 的字符串中包含 “流し満貫”，视为无 winning tile。
    # ---------------------------------------------------------
    is_nagashi = False
    for block in win_entries:
        for x in block:
            if isinstance(x, str) and "流し満貫" in x:
                is_nagashi = True
                break
    if is_nagashi:
        has_winning_tile = False

        # 流し満貫有赢家，但没有 winning tile
        return {
            "is_draw": False,
            "is_nagashi": True,
            "has_winning_tile": False,
            "winners": winners,
            "losers": losers,
            "score_delta": score_delta,
            "win_entries": win_entries
        }

    # ---------------------------------------------------------
    # 4. 正常荣和（包括一炮多响）
    # ---------------------------------------------------------
    return {
        "is_draw": False,
        "is_nagashi": False,
        "has_winning_tile": has_winning_tile,   # 普通自摸/荣和：True
        "winners": winners,
        "losers": losers,
        "score_delta": score_delta,
        "win_entries": win_entries
    }
def assign_winning_tiles(players, win_info):
    """
    根据 winners / losers 信息标记：
    - 自摸：M
    - 荣和：R（胡牌张），C（放铳标记）
    """
    winners = win_info.get("winners", [])
    losers = win_info.get("losers", [])

    # -------- 0. 流局 --------
    if not winners:
        return

    # -------- 1. 自摸（一个赢家 + 三个输家）--------
    #if len(winners) == 1 and len(losers) == 3:
    if winners == losers:
        w = winners[0]
        pw = players[w]
        # 胡牌张 = 摸牌行最后一张
        if pw["draws"]:
            win_tile = pw["draws"][-1]
        else:
            win_tile = ""

        if isinstance(win_tile, str) and win_tile:
            marked = "M" + win_tile
            pw["winning_tile"] = marked
            pw["is_winner"] = True

            # 修改摸牌行最后一张
            pw["draws"][-1] = marked

        return

    # -------- 2. 荣和（点炮）--------
    # 可一炮多响
    for w in winners:
        pw = players[w]
        pw["is_winner"] = True

        # 找点炮者（loser）
        # 可能对应多个，找与此 winner 匹配的 loser
        for loser_info in losers:
            loser = loser_info  # rotate_player_data 已经做好了
            pl = players[loser]

            # 取点炮家的最后一张舍牌
            if pl["discards"]:
                last_discard = pl["discards"][-1]
            else:
                last_discard = ""

            # 立直or抢杠判断
            is_chankan = isinstance(last_discard, str) and last_discard.startswith("k")
            is_riichi = isinstance(last_discard, str) and last_discard.startswith("r")

            if is_chankan:
                # 抢杠胡牌张 = 去掉 k 的部分
                tile = last_discard[1:]
                pw["winning_tile"] = "R" + tile
                # 抢杠不在舍牌上加 C
            if is_riichi:
                # 立直胡牌张 = 去掉 r 的部分
                tile = last_discard[1:]
                pw["winning_tile"] = "R" + tile
            else:
                # 普通荣和
                #if isinstance(last_discard, int):
                if last_discard=="d":
                    # 数字：用点炮家最后一张摸牌
                    if pl["draws"]:
                        tile = pl["draws"][-1]
                    else:
                        tile = ""
                    pl["draws"][-1] = "C" + tile
                else:
                    tile = last_discard
                    pl["discards"][-1] = "C" + tile
                pw["winning_tile"] = "R" + tile

                # 在点炮者舍牌上加 C（除抢杠）
                #if pl["discards"]:
                    
                

    return

def _tile_plain_str(tile):
    """
    去掉前导标记，返回如 '5m' / '0s' / '3z'。
    保留特殊 'N'/'d' 原样返回。
    """
    if tile is None:
        return None
    # convert numeric code if necessary
    if isinstance(tile, int):
        try:
            tile = convert_number_to_tile(tile)
        except Exception:
            tile = str(tile)

    if not isinstance(tile, str):
        return None

    if tile in ("N", "d"):
        return tile

    s = tile
    # remove leading alphabetic characters (t, tt, r, C, k, M, etc.)
    while s and s[0].isalpha():
        s = s[1:]
    return s if s != "" else None


def _tiles_equal_equiv(a, b):
    """
    比较两个纯 tile 字符串是否等价 (考虑 0 <-> 5 等价)。
    a,b 例： '5m', '0m', '3z'
    """
    if a is None or b is None:
        return False
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    if a == b:
        return True
    # both length at least 2
    if len(a) >= 2 and len(b) >= 2:
        ra, sa = a[:-1], a[-1]
        rb, sb = b[:-1], b[-1]
        if sa != sb:
            return False
        # equivalence for 0 and 5
        if (ra == '0' and rb == '5') or (ra == '5' and rb == '0'):
            return True
    return False


def remove_melds_from_final(hand, calls,):
    """
    从 hand (list of plain tile strings, e.g. '5m','0s'...) 中删除副露所占的牌。
    calls: list of call dicts, each dict expected to have either:
        - 'tiles': a list like ['t1p','2p','3p'] or ['tt8s','8s','8s'] etc.
          (these may include leading 't'/'tt' or other prefixes)
      OR
        - 'remaining' with an 'a' prefix indicating ankan (暗杠), e.g. 'a3z' or 'a51'
    函数会原地修改 hand（删除对应张数），并返回 None。
    """
    # Convert hand to a modifiable list (it may already be list)
    # We'll operate in-place on the provided list.
    # Helper to remove one tile matching target (with equivalence handling)
    def remove_one_match(target):
        """
        Try to remove one tile from hand matching target considering 0/5 equivalence.
        Return True if removed, False if not found.
        """
        # first direct match
        for i, h in enumerate(hand):
            if _tiles_equal_equiv(h, target):
                hand.pop(i)
                return True
        # try alternate (0<->5) only if explicit mismatch
        # already covered in _tiles_equal_equiv
        return False

    for c in calls:
        # Priority: if this call is an ankan (暗杠) indicated by c.get('remaining') starting with 'a'
        remaining = c.get("remaining")
        #print(f"remaining: {remaining}")
        if isinstance(remaining, str) and remaining.startswith('a'):
            # remove 3 tiles equal to remaining[1:]
            rem_tile = _tile_plain_str(remaining[1:])
            if rem_tile:
                for _ in range(3):
                    removed = remove_one_match(rem_tile)
                    # if not found just continue
            continue

        # Otherwise, look at tiles list if present
        tiles = c.get("tiles") or []
        if not tiles:
            # maybe c['remaining'] holds p/m form like 'p5s' - then parse
            if isinstance(remaining, str) and len(remaining) >= 2 and remaining[0] in ('p','m'):
                target = _tile_plain_str(remaining[1:])
                if target:
                    # typical pon/chi: need to remove corresponding tiles count
                    # we don't know count here; safest is to try remove 3 occurrences for pon-like
                    for _ in range(3):
                        remove_one_match(target)
            continue

        # Build a counts map from plain tile -> count to remove
        counts = {}
        for t in tiles:
            plain = _tile_plain_str(t)
            if plain is None:
                continue
            if plain in ('N', 'd'):
                continue
            counts[plain] = counts.get(plain, 0) + 1

        # If counts empty but remaining might indicate something (fallback)
        if not counts and isinstance(remaining, str) and len(remaining) >= 2 and remaining[0] in ('p','m'):
            plain = _tile_plain_str(remaining[1:])
            if plain:
                counts[plain] = counts.get(plain, 0) + 3

        # Now remove according to counts
        for plain_tile, cnt in counts.items():
            for _ in range(cnt):
                remove_one_match(plain_tile)

    # done (hand modified in-place)
    return

# 需要项目中已有： convert_number_to_tile(n) -> '5m' 等

def clean_tile_for_hand(tile):
    """
    清洗 tile 字符串，保留特殊单字 'd' 和 'N'，其他去掉前缀字母。
    如果是 int（数字编码），会调用 convert_number_to_tile。
    返回清洗后的字符串或 None。
    """
    if tile is None:
        return None

    # 数字编码 -> 转字符串
    if isinstance(tile, int):
        try:
            tile = convert_number_to_tile(tile)
        except Exception:
            # 如果没有该函数或转换失败，回退为 str(tile)
            tile = str(tile)

    # 保留 'd' 和 'N'（包括纯值和带前缀如 rd/rN 等形式）
    if tile == 'd' or tile == 'N':
        return tile

    # 如果是空或非字符串
    if not isinstance(tile, str):
        return None

    # 去掉前导字母标注 (如 r, C, R, k, M, t, p, m, a, j, ` 等)
    # 保留最后一位不剥离，防止吃掉 'd'/'N'（如 rd→d 而非 →""）
    s = tile
    while s and len(s) > 1 and s[0].isalpha():
        s = s[1:]
    s = s.strip()
    # 剥离前缀后可能剩 'd' 或 'N'（如 rd→d, CN→N）
    if s == 'd' or s == 'N':
        return s
    if s == '':
        return None
    return s


def tile_sort_key(tile):
    """
    把 tile 排序为 (suit_order, rank_index)：
      suit_order: m:0, p:1, s:2, z:3, others:4
      rank_index: 根据每个 suit 的自定义顺序：
         m/p/s: ['1','2','3','4','0','5','6','7','8','9']
         z:     ['1','2','3','4','5','6','7']
    tile: e.g. '5m', '0p', '7z'
    """
    if tile is None:
        return (100, 100)

    # If tile is numeric code (int), convert
    if isinstance(tile, int):
        try:
            tile = convert_number_to_tile(tile)
        except Exception:
            tile = str(tile)

    # remove any leading letters (safety)
    s = tile
    while s and s[0].isalpha():
        s = s[1:]
    if not s or len(s) < 2:
        return (100, 100)

    num_part = s[:-1]
    suit = s[-1]

    suit_order_map = {'m': 0, 'p': 1, 's': 2, 'z': 3}
    suit_idx = suit_order_map.get(suit, 4)

    if suit in ('m', 'p', 's'):
        order = ['1','2','3','4','0','5','6','7','8','9']
    elif suit == 'z':
        order = ['1','2','3','4','5','6','7']
    else:
        order = []

    # Find index; if not found, try numeric fallback
    try:
        rank_idx = order.index(num_part)
    except Exception:
        try:
            rank_idx = int(num_part) - 1
        except Exception:
            rank_idx = 999

    return (suit_idx, rank_idx, s)


def build_final_hand(player, is_tsumo=False):
    """
    根据 player 字段构建最终型（返回 list of cleaned tile strings，已排序）。
    player is dict assumed to contain:
      - "starting_hand": list of tiles (ints or strings)
      - "draws": list of tiles (ints or strings or 'N'/'d' etc)
      - "discards": list of tiles (ints or strings or 'N'/'d' etc)
    is_tsumo: bool, True if this player is the tsumo winner (最后一张 draw 已被用作胡牌张)
    """

    # make a working copy of starting hand (cleaned)
    hand = []
    for t in player.get("starting_hand", []):
        ct = clean_tile_for_hand(t)
        if ct and ct not in ('N', 'd'):
            hand.append(ct)

    draws = list(player.get("draws", []))
    discards = list(player.get("discards", []))

    rounds = max(len(draws), len(discards))
    for i in range(rounds):
        last_draw_clean = None

        # ---- 1) 摸牌阶段 ----
        if i < len(draws):
            raw_draw = draws[i]
            
            # If draw is integer code, convert inside clean_tile_for_hand
            draw_clean = clean_tile_for_hand(raw_draw)

            # If draw was 'N' -> skip
            if draw_clean == 'N' or draw_clean is None:
                last_draw_clean = None
            elif draw_clean == 'd':
                # 'd' shouldn't appear in draws normally, but treat as special: no append
                last_draw_clean = None
            else:
                # This is a real tile (e.g., '5m' or '0s')
                # If this is tsumo winner's last draw, skip appending (already in winning tile)
                if is_tsumo and (i == len(draws) - 1) and player["is_winner"]:
                    # do not append final tsumo tile into final hand
                    last_draw_clean = draw_clean
                else:
                    
                    hand.append(draw_clean)
                    last_draw_clean = draw_clean
                    #print(f"last_draw_clean: {last_draw_clean}")

        # ---- 2) 舍牌阶段 ----
        if i < len(discards):
            raw_discard = discards[i]

            # If discard is int, convert
            if isinstance(raw_discard, int):
                try:
                    raw_discard = convert_number_to_tile(raw_discard)
                except Exception:
                    raw_discard = str(raw_discard)

            # If discard is 'N' -> skip
            if raw_discard == 'N' or raw_discard is None:
                continue

            # If discard is 'd' (or prefixed like 'rd') -> means the player discarded
            # the tile they just drew (draws[i]). Strip prefix before checking.
            disc_stripped = raw_discard
            if isinstance(raw_discard, str):
                disc_stripped = clean_tile_for_hand(raw_discard)
            if disc_stripped == 'd':
                # remove the last_draw_clean (the tile we just appended from draws[i])
                if last_draw_clean and last_draw_clean in hand:
                    hand.remove(last_draw_clean)
                # else: nothing to remove
                continue

            # Otherwise, normal discard which may have prefixes (r,C,k,...)
            disc_clean = clean_tile_for_hand(raw_discard)

            # Special: if raw_discard starts with 'k' (added kong / chankan scenario),
            # we consider the actual tile as raw_discard[1:]
            if isinstance(raw_discard, str) and raw_discard.startswith('k'):
                # remove leading 'k' then clean remaining
                d2 = raw_discard[1:]
                disc_clean = clean_tile_for_hand(d2)

            # Remove one instance of disc_clean from hand if present
            if disc_clean and disc_clean in hand:
                hand.remove(disc_clean)
            else:
                # If not present, try a fallback: sometimes tile in hand has no leading zero vs five differences
                # e.g., hand may have '5m' while disc_clean is '0m' or vice versa.
                # Try to match by numeric & suit ignoring 0/5 difference:
                if isinstance(disc_clean, str) and len(disc_clean) >= 2:
                    suit = disc_clean[-1]
                    rank = disc_clean[:-1]
                    # try to match alternative of 0<->5
                    alt = None
                    if rank == '0':
                        alt = '5' + suit
                    elif rank == '5':
                        alt = '0' + suit
                    if alt and alt in hand:
                        hand.remove(alt)
                    # else nothing to remove

        # ... build hand (unsorted) above ...
    # remove meld tiles (calls should be list of call dicts attached to player)
    calls = player.get("calls", [])
    #all_calls = player.get("all_calls", [])
    #call_events = player.get("call_events", [])
    #calls_x=calls
    
    # calls may be in various formats; ensure it's list of dicts with 'tiles' or 'remaining'
    remove_melds_from_final(hand, calls)

    hand_sorted = sorted(hand, key=tile_sort_key)
    return hand_sorted

def parse_antoinput_file(file_path):
    """解析antoinput.json文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    #===============================
    # 解析游戏基本信息
    #===============================
    title = data['title'][0] if len(data['title']) > 0 else ""
    date = data['title'][1] if len(data['title']) > 1 else datetime.datetime.now().strftime('%Y.%m.%d')

    log_data = data['log'][0]
    round_info_data = log_data[0]

    # 局数
    round_num = round_info_data[0]
    if 0 <= round_num <= 3:
        round_name = f"东{round_num+1}局"
    elif 4 <= round_num <= 7:
        round_name = f"南{round_num-3}局"
    else:
        round_name = "东一局"

    honba = round_info_data[1]
    round_info = f"{round_name}{honba}本场"

    # 场供
    deposit_points = round_info_data[2] * 1000
    deposits = f"场供：{deposit_points}"

    #===============================
    # 宝牌
    #===============================
    dora_indicators = log_data[2]
    uradora_indicators = log_data[3]

    dora_list = [get_dora_tile(ind) for ind in dora_indicators]
    uradora_list = [get_dora_tile(ind) for ind in uradora_indicators]

    if len(dora_list) < 5: dora_list += ['']*(5-len(dora_list))
    if len(uradora_list) < 5: uradora_list += ['']*(5-len(uradora_list))

    #===============================
    # 初始分、最终分变化（未合并）
    #===============================
    initial_scores = log_data[1]

    # 这里 final_scores 是每名玩家的最终加减
    # 但 log_data[-1] 很复杂 → 我们将使用 parse_winner_and_scores 来解析
    raw_last = log_data[-1]
    win_info = parse_winner_and_scores(raw_last)
    #print(win_info)
    # 合并后的点数变化
    raw_winners = win_info["winners"]        # 例如 [0,1,2]
    raw_losers  = win_info["losers"]         # 例如 [3,3,3]
    final_scores = win_info["score_delta"]   # [p0,p1,p2,p3]

    #===============================
    # 解析玩家 raw 数据
    #===============================
    player_data_start = 4
    raw_player_data = []
    for i in range(4):
        starting_hand_data = log_data[player_data_start + i*3]
        draws_data = log_data[player_data_start + i*3 + 1]
        discards_data = log_data[player_data_start + i*3 + 2]
        raw_player_data.append({
            'starting_hand': starting_hand_data,
            'draws': draws_data,
            'discards': discards_data
        })
       # ---------------------------------------------------------
    # ★ 计算立直棒（每次出现 r… 扣 1000 点）
    # ---------------------------------------------------------
    riichi_payments = [0, 0, 0, 0]  # 对应 4 个玩家（未旋转前）

    for i in range(4):
        discards = log_data[player_data_start + i*3 + 2]  # 每位玩家的舍牌行
        for item in discards:
            if isinstance(item, str) and item.startswith("r"):
                riichi_payments[i] -= 1000   # 立直棒支付 1000

    # 最终分数变化中加入立直棒扣除
    # final_scores 是 log_data 最后一段的得失点（未旋转）
    adjusted_final_scores = [
        final_scores[i] + riichi_payments[i] for i in range(4)
    ]


    #===============================
    # 按局数旋转玩家
    #===============================
    names = data['name']
    rotated_names, rotated_initial_scores, rotated_final_scores, rotated_player_data,rotated_win_info, rotated_loser_info= rotate_player_data(
        round_num, names, initial_scores, raw_player_data, adjusted_final_scores,raw_winners, raw_losers
)

    win_info["winners"] = rotated_win_info
    win_info["losers"] = rotated_loser_info

    # -------------------------
    # 在解析副露前统一处理“跳过”插入 N
    # 我们先从 rotated_player_data 中提取 all_draws / all_discards（浅拷贝）
    # 并收集所有副露事件 (player, index, call_str)
    # 然后调用 insert_skips_for_calls 修改 all_draws / all_discards（in-place）
    # -------------------------
    all_draws = [list(p['draws']) for p in rotated_player_data]
    all_discards = [list(p['discards']) for p in rotated_player_data]

    all_calls = []
    for pi in range(4):
        for idx_d, cell in enumerate(rotated_player_data[pi]['draws']):
            if isinstance(cell, str) and any(ch in cell for ch in ('p','m','k','a')):
                all_calls.append({"player": pi, "index": idx_d, "call_str": cell, "remaining": rotated_player_data[pi]['draws'][idx_d]})
                #print(idx_d)
        for idx_dis, cell in enumerate(rotated_player_data[pi]['discards']):
            if isinstance(cell, str) and any(ch in cell for ch in ('p','m','k','a')):
                all_calls.append({"player": pi, "index": idx_dis, "call_str": cell, "remaining": rotated_player_data[pi]['discards'][idx_dis]})


    # 调用插入函数（这会就地修改 all_draws / all_discards）
    insert_skips_advanced(all_draws, all_discards, all_calls)


    #print(win_info)
    #===============================
    # 解析玩家（结合 winner 信息）
    #===============================
    players = []
    positions = ["东","南","西","北"]

    winners_set = set(win_info["winners"]) if win_info["winners"] else set()
    losers_set  = set(win_info["losers"]) if win_info["losers"] else set()
    has_win_tile = win_info["has_winning_tile"]
    is_draw = win_info["is_draw"]
    is_nagashi = win_info["is_nagashi"]

    # winning tile 来自谁？
    # 规则：荣和（点炮） → 胡牌张就是点炮者最后舍牌
    #      自摸（losers 全为空）→ 胡牌张就是 winner 自己最后摸牌（未实现复杂判断）
    # 这里先简单化：荣和场合按 discards[-1] 取（你之前的逻辑）
    # 自摸可进一步完善，但你当前项目暂不要求
    ron_winning_tile = {}

    if has_win_tile and not is_draw and not is_nagashi:
        # 多个赢 → 每个 winner 对应各自的 loser
        for w, l in zip(win_info["winners"], win_info["losers"]):
            # 胡的是点炮者最后一张
            raw_discards = rotated_player_data[l]["discards"]
            # 找最后一张舍牌
            if raw_discards:
                last_tile_raw = raw_discards[-1]
            else:
                last_tile_raw = None
            if isinstance(last_tile_raw, int):
                last_tile_raw = convert_number_to_tile(last_tile_raw)
            ron_winning_tile[w] = last_tile_raw

    #===============================
    # 构建 player 对象
    #===============================
    for i in range(4):
        pdata = rotated_player_data[i]

        # starting hand
        starting_hand = [convert_number_to_tile(x) for x in pdata['starting_hand'] if isinstance(x, int)]

                # 使用插入 N 后的 all_draws / all_discards（注意：all_draws 已在上面构建）
        draws = all_draws[i].copy()
        discards = all_discards[i].copy()

        # 现在解析副露（process_player_calls 仍接受 draws, discards）
        calls, riichi_index ,call_events= process_player_calls(draws, discards)

        # 再把数字转为 tile 字符串（仅对数字项转换）
        draws = [convert_number_to_tile(x) if isinstance(x, int) else x for x in draws]
        discards = [convert_number_to_tile(x) if isinstance(x, int) else x for x in discards]


        name = rotated_names[i] if i < len(rotated_names) else f"玩家{i+1}"
        position = positions[i]

        score_before = rotated_initial_scores[i]
        score_after  = score_before + rotated_final_scores[i]

        #===============================
        # Winner 判定
        #===============================
        is_winner = False
        winning_tile = None

        if not is_draw and not is_nagashi and i in winners_set:
            is_winner = True
            winning_tile = ron_winning_tile.get(i, None)

       
        #===============================
        # 构建字典
        #===============================
        player = {
            "position": position,
            "name": name,
            "score_before": score_before,
            "score_after": score_after,
            "starting_hand": starting_hand,
            "draws": draws,
            "discards": discards,
            "riichi_index": riichi_index,
            "calls": calls,
            "final_hand": starting_hand.copy(),   # TODO: 可改为真实 final hand 计算
            "is_winner": is_winner
        }

        if is_winner and winning_tile:
            player["winning_tile"] = winning_tile

        players.append(player)
        # 处理胡牌张、自摸/荣和标记
         # 判断该玩家是否为自摸（例如你用 M 前缀标注）
        if win_info["winners"] == win_info["losers"]:
             is_tsumo = True
        else:
            is_tsumo = False
        wt = player.get("winning_tile")
        #if isinstance(wt, str) and wt.startswith("M"):
            #is_tsumo = True

        player["final_hand"] = build_final_hand(player, is_tsumo=is_tsumo)

    assign_winning_tiles(players, win_info)
    #===============================
    # 构建游戏对象
    #===============================
    game = MahjongGame(
        title=title,
        date=date,
        round_info=round_info,
        deposits=deposits,
        dora1=dora_list[0], dora2=dora_list[1], dora3=dora_list[2], dora4=dora_list[3], dora5=dora_list[4],
        uradora1=uradora_list[0], uradora2=uradora_list[1], uradora3=uradora_list[2],
        uradora4=uradora_list[3], uradora5=uradora_list[4],
        players=players
    )

    return game


def parse_input_file(file_path):
    """解析输入文本文件"""
    config = configparser.ConfigParser()
    config.read(file_path, encoding='utf-8')
    
    # 解析游戏信息
    game_section = config['Game']
    dora = game_section['dora'].split(',')
    uradora = game_section['uradora'].split(',')
    
    # 确保有5个宝牌和里宝牌
    if len(dora) < 5:
        dora += [''] * (5 - len(dora))
    if len(uradora) < 5:
        uradora += [''] * (5 - len(uradora))
    
    players = []
    for i in range(1, 5):
        player_section = config[f'Player{i}']
        
        # 处理calls字段
        calls_str = player_section.get('calls', '[]')
        try:
            calls = ast.literal_eval(calls_str)
        except:
            print(f"警告: 无法解析玩家{i}的calls字段: {calls_str}")
            calls = []

       # 使用增强解析器处理牌谱字段
        starting_hand = parse_tile_string(player_section.get('starting_hand', '[]'))
        draws = parse_tile_string(player_section.get('draws', '[]'))
        discards = parse_tile_string(player_section.get('discards', '[]'))
        final_hand = parse_tile_string(player_section.get('final_hand', '[]'))

        # 构建玩家字典
        player = {
            "position": player_section['position'],
            "name": player_section['name'],
            "score_before": int(player_section['score_before']),
            "score_after": int(player_section['score_after']),
            "starting_hand": starting_hand,
            "draws": draws,
            "discards": discards,
            "riichi_index": int(player_section['riichi_index']),
            "calls": [{"tiles": call} for call in calls],
            "final_hand": final_hand,
            "is_winner": player_section.getboolean('is_winner'),
        }
        
        if player['is_winner']:
            player['winning_tile'] = player_section['winning_tile']
        
        players.append(player)
    
    # 创建游戏对象
    game = MahjongGame(
        title=game_section['title'],
        date=game_section['date'],
        round_info=game_section['round_info'],
        deposits=game_section['deposits'],
        dora1=dora[0], dora2=dora[1], dora3=dora[2], dora4=dora[3], dora5=dora[4],
        uradora1=uradora[0], uradora2=uradora[1], uradora3=uradora[2], 
        uradora4=uradora[3], uradora5=uradora[4],
        players=players
    )
    
    # 设置玩家行位置
    game.player_start_positions = [
        (55.3, 51.3),   # 东家
        (55.3, 108.3),  # 南家
        (55.3, 165.2),  # 西家
        (55.3, 222.3)   # 北家
    ]
    
    # 设置行高
    game.player_row_heights = [12, 12, 12, 12]
    
    return game

def generate_pdf_from_json(json_path, output_pdf):
    """
    json_path: JSON 文件路径（字符串）
    output_pdf: 输出 PDF 路径
    """

    try:
        # 使用你的原生解析函数（它需要文件路径）
        game = parse_antoinput_file(json_path)

        # 调用生成 PDF
        game.create_pdf_with_annotations(output_pdf)

        return True, ""

    except Exception as e:
        import traceback
        return False, traceback.format_exc()


def split_hanchan_rounds(json_path):
    """读取半庄JSON, 把log[]中的每一局拆分为单局格式的dict列表"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rounds = []
    title = data.get("title", ["", ""])
    name = data.get("name", [])
    rule = data.get("rule", {})
    log = data.get("log", [])
    for i, round_log in enumerate(log):
        single = {
            "title": [title[0] if len(title) > 0 else "",
                      title[1] if len(title) > 1 else ""],
            "name": name,
            "rule": rule,
            "log": [round_log],
        }
        rounds.append(single)
    return rounds


def generate_pdfs_from_hanchan(json_path, output_dir, gen_individual=True):
    """
    从半庄JSON生成PDF。
    json_path: 半庄格式JSON路径
    output_dir: 输出目录
    gen_individual: 是否保留单局PDF文件
    返回 {"merged": path | None, "individuals": [path, ...]}
    """
    rounds = split_hanchan_rounds(json_path)

    # 提取主标题
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    main_title = data.get("title", ["score_sheet", ""])[0] or "score_sheet"

    individual_paths = []
    tmp_files = []

    for i, rd in enumerate(rounds, 1):
        # 写临时JSON
        tmpf = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", mode="w", encoding="utf-8")
        json.dump(rd, tmpf, ensure_ascii=False, indent=2)
        tmpf.close()
        tmp_files.append(tmpf.name)

        # 解析并生成PDF
        try:
            game = parse_antoinput_file(tmpf.name)
            pdf_path = os.path.join(output_dir, f"round_{i}.pdf")
            game.create_pdf_with_annotations(pdf_path)
            individual_paths.append(pdf_path)
        except Exception as e:
            import traceback
            print(f"Round {i} failed: {traceback.format_exc()}")
            # Cleanup temps and raise
            for t in tmp_files:
                try: os.remove(t)
                except: pass
            raise

    # 清理临时JSON
    for t in tmp_files:
        try: os.remove(t)
        except: pass

    # 合并整合PDF
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    merged_path = os.path.join(output_dir, f"{main_title}_{ts}.pdf")

    from PyPDF2 import PdfMerger
    merger = PdfMerger()
    try:
        for p in individual_paths:
            merger.append(p)
        merger.write(merged_path)
    finally:
        merger.close()

    # 如果不保留单局，删除
    if not gen_individual:
        for p in individual_paths:
            try: os.remove(p)
            except: pass
        individual_paths = []

    return {"merged": merged_path, "individuals": individual_paths}

def main():
    if len(sys.argv) != 2:
        print("用法: python mahjong_score_sheet.py input.txt 或 antoinput.json")
        print("示例: python mahjong_score_sheet.py example.txt")
        print("示例: python mahjong_score_sheet.py antoinput.json")
        return
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"错误: 文件 '{input_file}' 不存在")
        return
    
    try:
        if input_file.endswith('.json'):
            game = parse_antoinput_file(input_file)
        else:
            game = parse_input_file(input_file)
    except Exception as e:
        print(f"解析输入文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 创建输出目录
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_dir, f"麻將牌谱_{timestamp}.pdf")
    
    try:
        game.create_pdf_with_annotations(filename)
        print(f"牌谱已生成: {filename}")
    except Exception as e:
        print(f"生成PDF时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()