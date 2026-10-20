import sys
import random
import numpy as np
import pygame
import pymunk

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================
ANCHO, ALTO = 1150, 750
FPS = 60

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("🎮 Simulación Baloto 2D - Cilindro con Esquinas Redondeadas")
reloj = pygame.time.Clock()

# ==========================================
# MOTOR FISICO INICIO
# ==========================================
espacio = pymunk.Space()
espacio.gravity = (0, 680)
espacio.iterations = 30

# ------------------------------------------
# 1. TÓMBOLA 1: CILINDRO CON BASE REDONDEADA
# ------------------------------------------
def crear_cilindro_redondeado(centro_x, base_y, ancho_cil, alto_cil, radio_esquina=35):
    """Crea un cilindro con esquinas inferiores redondeadas/biseladas para evitar estancamiento."""
    ANCHO_TUBO = 30
    ALTURA_TUBO = 70
    x_izq = centro_x - ancho_cil // 2
    x_der = centro_x + ancho_cil // 2
    y_top = base_y - alto_cil

    puntos = []
    # Tubo superior
    puntos.append((centro_x - ANCHO_TUBO, ALTURA_TUBO))
    # Embudo superior izquierdo
    puntos.append((centro_x - ANCHO_TUBO, y_top))
    puntos.append((x_izq, y_top))
    # Pared vertical izquierda hasta antes de la curva
    puntos.append((x_izq, base_y - radio_esquina))
    
    # Curva / Bisel esquina inferior izquierda
    puntos.append((x_izq + radio_esquina, base_y))
    
    # Base plana central
    puntos.append((x_der - radio_esquina, base_y))
    
    # Curva / Bisel esquina inferior derecha
    puntos.append((x_der, base_y - radio_esquina))
    
    # Pared vertical derecha
    puntos.append((x_der, y_top))
    # Embudo superior derecho
    puntos.append((centro_x + ANCHO_TUBO, y_top))
    puntos.append((centro_x + ANCHO_TUBO, ALTURA_TUBO))

    for i in range(len(puntos) - 1):
        seg = pymunk.Segment(espacio.static_body, puntos[i], puntos[i+1], 8)
        seg.elasticity = 0.85
        seg.friction = 0.05  # Menor fricción en bordes
        espacio.add(seg)

    techo = pymunk.Segment(espacio.static_body, (centro_x - ANCHO_TUBO, ALTURA_TUBO), (centro_x + ANCHO_TUBO, ALTURA_TUBO), 8)
    techo.elasticity = 0.2
    espacio.add(techo)

# ------------------------------------------
# 2. TÓMBOLA 2: ESFERA (Superbalota)
# ------------------------------------------
def crear_esfera_real(centro_x, centro_y, radio):
    ANCHO_TUBO = 30
    ALTURA_TUBO = 70
    sin_theta = ANCHO_TUBO / radio
    theta_corte = np.arcsin(sin_theta)
    
    ang_izq = np.pi / 2 + theta_corte
    ang_der = np.pi / 2 - theta_corte
    
    puntos = [(centro_x - ANCHO_TUBO, ALTURA_TUBO)]
    y_union = centro_y - np.sqrt(radio**2 - ANCHO_TUBO**2)
    puntos.append((centro_x - ANCHO_TUBO, y_union))
    
    num_segs = 50
    for i in range(num_segs + 1):
        t = ang_izq + (2 * np.pi - (ang_izq - ang_der)) * (i / num_segs)
        x = centro_x + radio * np.cos(t)
        y = centro_y - radio * np.sin(t)
        puntos.append((x, y))
        
    puntos.append((centro_x + ANCHO_TUBO, y_union))
    puntos.append((centro_x + ANCHO_TUBO, ALTURA_TUBO))
    
    for i in range(len(puntos) - 1):
        seg = pymunk.Segment(espacio.static_body, puntos[i], puntos[i+1], 8)
        seg.elasticity = 0.85
        seg.friction = 0.05
        espacio.add(seg)

    techo = pymunk.Segment(espacio.static_body, (centro_x - ANCHO_TUBO, ALTURA_TUBO), (centro_x + ANCHO_TUBO, ALTURA_TUBO), 8)
    techo.elasticity = 0.2
    espacio.add(techo)

# ==========================================
# DIMENSIONES Y POSICIONAMIENTO
# ==========================================
CENTRO_CILINDRO_X = 380
BASE_CILINDRO_Y = 620
ANCHO_CIL = 260
ALTO_CIL = 360
RADIO_ESQUINA = 40 

CENTRO_T2 = (880, 440)
RADIO_T2 = 150

crear_cilindro_redondeado(CENTRO_CILINDRO_X, BASE_CILINDRO_Y, ANCHO_CIL, ALTO_CIL, RADIO_ESQUINA)
crear_esfera_real(CENTRO_T2[0], CENTRO_T2[1], RADIO_T2)

# ==========================================
# CREACIÓN DE BALOTAS
# ==========================================
balotas_p = []
balotas_sb = []

# Balotas Principales (43)
for i in range(1, 44):
    momento = pymunk.moment_for_circle(1.0, 0, 11)
    cuerpo = pymunk.Body(1.0, momento)
    cuerpo.position = (CENTRO_CILINDRO_X + random.randint(-70, 70), BASE_CILINDRO_Y - random.randint(20, 70))
    cuerpo.velocity_limit = 700
    forma = pymunk.Circle(cuerpo, 11)
    forma.elasticity = 0.88; forma.friction = 0.05
    espacio.add(cuerpo, forma)
    balotas_p.append({"num": i, "body": cuerpo, "capturada": False})

# Superbalotas (16)
for i in range(1, 17):
    momento = pymunk.moment_for_circle(1.0, 0, 11)
    cuerpo = pymunk.Body(1.0, momento)
    cuerpo.position = (CENTRO_T2[0] + random.randint(-40, 40), CENTRO_T2[1] + random.randint(20, 60))
    cuerpo.velocity_limit = 700
    forma = pymunk.Circle(cuerpo, 11)
    forma.elasticity = 0.88; forma.friction = 0.05
    espacio.add(cuerpo, forma)
    balotas_sb.append({"num": i, "body": cuerpo, "capturada": False})

capturadas_p = []
capturada_sb = []

# ==========================================
# FUERZAS DE AIRE
# ==========================================
def aplicar_fuerzas():
    # 1. CILINDRO PRINCIPAL
    if len(capturadas_p) < 5:
        for b in balotas_p:
            if b["capturada"]: continue
            pos = b["body"].position
            
            # Impulso desde el fondo
            if pos.y > BASE_CILINDRO_Y - 180:
                fuerza_y = random.uniform(-1850, -1150)
                fuerza_x = random.uniform(-280, 280)
                
                # Empuje antistack lateral si se arriman a las esquinas redondeadas
                if pos.x < CENTRO_CILINDRO_X - ANCHO_CIL // 2 + RADIO_ESQUINA + 20:
                    fuerza_x += random.uniform(300, 600)  # Empuja hacia el centro
                elif pos.x > CENTRO_CILINDRO_X + ANCHO_CIL // 2 - RADIO_ESQUINA - 20:
                    fuerza_x -= random.uniform(300, 600)  # Empuja hacia el centro
                    
                b["body"].apply_force_at_local_point((fuerza_x, fuerza_y))
            
            # Succión en la zona alta
            y_top_cil = BASE_CILINDRO_Y - ALTO_CIL
            if pos.y < y_top_cil + 110 and abs(pos.x - CENTRO_CILINDRO_X) < 65:
                dx = CENTRO_CILINDRO_X - pos.x
                b["body"].apply_force_at_local_point((dx * 55, -4200))

    # 2. ESFERA SUPERBALOTA
    if len(capturada_sb) < 1:
        for b in balotas_sb:
            if b["capturada"]: continue
            pos = b["body"].position
            
            fuerza_y = random.uniform(-1350, -800)
            fuerza_x = random.uniform(-250, 250)
            b["body"].apply_force_at_local_point((fuerza_x, fuerza_y))
            
            if pos.y < CENTRO_T2[1] - RADIO_T2 + 65 and abs(pos.x - CENTRO_T2[0]) < 40:
                dx = CENTRO_T2[0] - pos.x
                b["body"].apply_force_at_local_point((dx * 50, -3600))

# ==========================================
# BUCLE PRINCIPAL
# ==========================================
ejecutando = True
while ejecutando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_r:
            capturadas_p.clear(); capturada_sb.clear()
            for b in balotas_p:
                b["body"].position = (CENTRO_CILINDRO_X + random.randint(-70, 70), BASE_CILINDRO_Y - random.randint(20, 70))
                b["body"].velocity = (0, 0); b["capturada"] = False
            for b in balotas_sb:
                b["body"].position = (CENTRO_T2[0] + random.randint(-40, 40), CENTRO_T2[1] + random.randint(20, 60))
                b["body"].velocity = (0, 0); b["capturada"] = False

    aplicar_fuerzas()
    espacio.step(1.0 / FPS)

    # Capturas en recámaras
    if len(capturadas_p) < 5:
        for b in balotas_p:
            if not b["capturada"] and b["body"].position.y < 110 and abs(b["body"].position.x - CENTRO_CILINDRO_X) < 28:
                b["capturada"] = True
                capturadas_p.append(b["num"])

    if len(capturada_sb) < 1:
        for b in balotas_sb:
            if not b["capturada"] and b["body"].position.y < 110 and abs(b["body"].position.x - CENTRO_T2[0]) < 28:
                b["capturada"] = True
                capturada_sb.append(b["num"])

    # --- RENDERIZADO ---
    pantalla.fill((16, 20, 28))

    # Render Cilindro Izquierdo (Esquinas Suaves)
    x_i = CENTRO_CILINDRO_X - ANCHO_CIL // 2
    x_d = CENTRO_CILINDRO_X + ANCHO_CIL // 2
    y_t = BASE_CILINDRO_Y - ALTO_CIL
    r_e = RADIO_ESQUINA

    pygame.draw.line(pantalla, (45, 55, 75), (x_i, y_t), (x_i, BASE_CILINDRO_Y - r_e), 4) # Pared izq
    pygame.draw.line(pantalla, (45, 55, 75), (x_i, BASE_CILINDRO_Y - r_e), (x_i + r_e, BASE_CILINDRO_Y), 4) # Esquina izq
    pygame.draw.line(pantalla, (45, 55, 75), (x_i + r_e, BASE_CILINDRO_Y), (x_d - r_e, BASE_CILINDRO_Y), 4) # Base
    pygame.draw.line(pantalla, (45, 55, 75), (x_d - r_e, BASE_CILINDRO_Y), (x_d, BASE_CILINDRO_Y - r_e), 4) # Esquina der
    pygame.draw.line(pantalla, (45, 55, 75), (x_d, BASE_CILINDRO_Y - r_e), (x_d, y_t), 4) # Pared der
    pygame.draw.line(pantalla, (45, 55, 75), (x_i, y_t), (CENTRO_CILINDRO_X - 30, y_t), 4) # Embudo izq
    pygame.draw.line(pantalla, (45, 55, 75), (x_d, y_t), (CENTRO_CILINDRO_X + 30, y_t), 4) # Embudo der

    # Render Esfera Derecha
    pygame.draw.circle(pantalla, (45, 55, 75), CENTRO_T2, RADIO_T2, 4)

    # Tubos visuales
    pygame.draw.rect(pantalla, (35, 45, 65), (CENTRO_CILINDRO_X - 30, 70, 60, y_t - 70), 3)
    pygame.draw.rect(pantalla, (35, 45, 65), (CENTRO_T2[0] - 30, 70, 60, CENTRO_T2[1] - RADIO_T2 - 70), 3)

    # Render Balotas Rojas
    for b in balotas_p:
        pos = (int(b["body"].position.x), int(b["body"].position.y))
        color = (110, 110, 110) if b["capturada"] else (235, 70, 70)
        pygame.draw.circle(pantalla, color, pos, 11)
        pygame.draw.circle(pantalla, (255, 255, 255), pos, 11, 1)
        fuente = pygame.font.SysFont("Arial", 10, bold=True)
        txt = fuente.render(f"{b['num']:02d}", True, (255, 255, 255) if not b["capturada"] else (200, 200, 200))
        pantalla.blit(txt, txt.get_rect(center=pos))

    # Render Superbalotas Doradas
    for b in balotas_sb:
        pos = (int(b["body"].position.x), int(b["body"].position.y))
        color = (110, 110, 110) if b["capturada"] else (240, 190, 40)
        pygame.draw.circle(pantalla, color, pos, 11)
        pygame.draw.circle(pantalla, (255, 255, 255), pos, 11, 1)
        fuente = pygame.font.SysFont("Arial", 10, bold=True)
        txt = fuente.render(f"{b['num']:02d}", True, (10, 10, 10) if not b["capturada"] else (200, 200, 200))
        pantalla.blit(txt, txt.get_rect(center=pos))

    # --- PANEL HUD SUPERIOR ---
    pygame.draw.rect(pantalla, (24, 30, 42), (0, 0, ANCHO, 65))
    pygame.draw.line(pantalla, (0, 200, 255), (0, 65), (ANCHO, 65), 2)

    fuente_hud = pygame.font.SysFont("Consolas", 15, bold=True)
    pantalla.blit(fuente_hud.render("CILINDRO PRINCIPAL (1-43):", True, (200, 220, 255)), (25, 22))
    
    for k in range(5):
        val = f"{capturadas_p[k]:02d}" if k < len(capturadas_p) else "--"
        col_box = (220, 60, 60) if k < len(capturadas_p) else (45, 55, 75)
        pygame.draw.rect(pantalla, col_box, (260 + k*55, 12, 45, 40), border_radius=6)
        txt_k = fuente_hud.render(val, True, (255, 255, 255))
        pantalla.blit(txt_k, txt_k.get_rect(center=(282 + k*55, 32)))

    pantalla.blit(fuente_hud.render("SUPERBALOTA (1-16):", True, (255, 215, 0)), (620, 22))
    val_sb = f"{capturada_sb[0]:02d}" if len(capturada_sb) > 0 else "--"
    col_sb = (230, 170, 20) if len(capturada_sb) > 0 else (45, 55, 75)
    pygame.draw.rect(pantalla, col_sb, (820, 12, 45, 40), border_radius=6)
    txt_sb = fuente_hud.render(val_sb, True, (10, 10, 10) if len(capturada_sb) > 0 else (255, 255, 255))
    pantalla.blit(txt_sb, txt_sb.get_rect(center=(842, 32)))

    pantalla.blit(fuente_hud.render("[R] Reiniciar", True, (150, 160, 180)), (1000, 22))

    pygame.display.flip()
    reloj.tick(FPS)

pygame.quit()
sys.exit()
