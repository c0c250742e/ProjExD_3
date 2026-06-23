import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

class Score:
    def __init__(self):
        self.fonto = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def update(self, screen):
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)
        
class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        # 合計移動量が [0, 0] でないとき、向きを更新する
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        # こうかとんの向きを速度（vx, vy）に代入
        self.vx, self.vy = bird.dire
        
        # 角度を計算して画像を回転
        theta = math.atan2(-self.vy, self.vx)
        angle = math.degrees(theta)
        self.img = pg.transform.rotozoom(pg.image.load("fig/beam.png"), angle, 1.0)
        
        self.rct = self.img.get_rect()
        
        # こうかとんの向きに合わせて初期位置を中心からずらす
        self.rct.centerx = bird.rct.centerx + bird.rct.width  * self.vx / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy / 5

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        """
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)  


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Explosion:
    """
    爆弾が撃ち落とされたときの爆発エフェクトに関するクラス
    """
    def __init__(self, bomb: Bomb, life: int):
        img = pg.image.load("fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, True, True)]
        self.img  = self.imgs[0]
        self.rct  = self.img.get_rect()
        self.rct.center = bomb.rct.center
        self.life = life

    def update(self, screen: pg.Surface):
        self.life -= 1
        if self.life > 0:
            self.img = self.imgs[self.life // 5 % 2]  # 5フレームごとに反転
            screen.blit(self.img, self.rct)

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams = []  # 単発から空リストに変更
    score = Score() # スコアクラスのインスタンスを作成
    exps = []  # 爆発エフェクトのリストを追加
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))  # リストにビームを追加する          
        screen.blit(bg_img, [0, 0])
        
        # 1. こうかとんと爆弾の衝突判定
        for bomb in bombs:
            if bomb is not None: # Noneチェック
                if bird.rct.colliderect(bomb.rct):
                    # ゲームオーバー時に，こうかとん画像を切り替え
                    bird.change_img(8, screen)

                    # 【練習4追加】ゲームオーバーの文字を表示
                    fonto = pg.font.Font(None, 80)
                    txt = fonto.render("Game Over", True, (255, 0, 0))
                    # 画面中央付近に配置
                    screen.blit(txt, [WIDTH//2-150, HEIGHT//2])

                    pg.display.update()
                    time.sleep(1)
                    return

        # キー入力とこうかとんのアップデート
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        # 【追加課題2】すべてのビームを移動・描画する
        for bm in beams:
            if bm is not None:
                bm.update(screen)
        
        # 【追加課題2】画面内にいるビームだけをリストに残す（画面外に出たら消去）
        beams = [bm for bm in beams if bm is not None and check_bound(bm.rct) == (True, True)]

        # 2. 当たった爆弾やビームをNoneにする（2重ループ）
        for i, bomb in enumerate(bombs):
            for j, bm in enumerate(beams):
                if bomb is not None and bm is not None:
                    if bm.rct.colliderect(bomb.rct):
                        # 衝突した爆弾の位置に寿命50フレームの爆発を生成
                        exps.append(Explosion(bomb, 50))
                        bombs[i] = None   # 爆弾を消す印
                        beams[j] = None   # ビームを消す印
                        score.score += 1  # スコアを加算

        # 【超重要】印（None）がついた爆弾とビームをリストから完全に削除する
        bombs = [bomb for bomb in bombs if bomb is not None]
        beams = [bm for bm in beams if bm is not None]

        # 3. 生き残っている爆弾のみ位置更新と描画を行う
        for bomb in bombs:
            bomb.update(screen)

        # 爆発エフェクトの移動・描画
        for exp in exps:
            exp.update(screen)
        # 寿命（life）が0より大きいものだけをリストに残す
        exps = [exp for exp in exps if exp.life > 0]

        score.update(screen) # スコアの更新と描画

        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
