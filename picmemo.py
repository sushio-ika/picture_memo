import tkinter as tk
from tkinter import Menu, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk,ImageEnhance
import json
import os

inserted_images = {}
current_filepath = None#現在開いているファイルのパス
modified = False
selected_font_size = None#フォントサイズを保持する変数
selected_image_name_for_highlight = None#現在ハイライトされている画像の名前
#デフォルトの文字色をカラーコードで保存
default_font_color = "#000000"  #黒色

HIGHLIGHT_BRIGHTNESS_FACTOR = 0.7#明るさ倍率
HIGHLIGHT_OPACITY_FACTOR = 0.7#透明度倍率

PICTURE_WIDTH = 300#画像の横幅を固定

# --- 関数定義 ---
#ファイル編集系
def new_file():
    """新規ファイルを作成"""
    global current_filepath,modified

    if modified:#ファイル内容が変更されていた場合
        result = messagebox.askyesnocancel("確認", "変更内容を保存しますか？")
        if result is None:#キャンセルが選択された場合
            return
        elif result:#はいが選択された場合
            save_file(overwrite=True)

    main_memo.delete(1.0, tk.END)#テキストをクリア
    main_memo.edit_modified(False)

    form.title("ピクメモ")
    current_filepath = None#新規作成なのでパスはクリア

    main_memo.config(foreground=default_font_color)
    change_font_size(12)#デフォルトのフォントサイズに設定
    main_memo.focus_set()#カーソルを自動でセット
    modified = False#編集状態をリセット

def open_file():
    """ファイルを開く"""
    global current_filepath,modified
    
    filepath = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )

    if not filepath:
        return
    
    current_filepath = filepath#ファイルパスを更新

    try:
        if modified:#ファイル内容が変更されていた場合
            result = messagebox.askyesnocancel("確認", "変更内容を保存しますか？")
            if result is None:#キャンセルが選択された場合
                return
            elif result:#はいが選択された場合
                save_file(overwrite=True)

        main_memo.delete(1.0, tk.END)#テキストをクリア
        inserted_images.clear()#画像参照をクリア

        with open(current_filepath, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        
        main_memo.config(foreground=default_font_color)#デフォルトの文字色を設定

        if "font_size" in loaded_data:#フォントサイズが指定されている場合
            change_font_size(loaded_data["font_size"])
        else:
            change_font_size(12)#デフォルトサイズ

        
        main_memo.edit_reset()
        main_memo.config(undo=False)#Undo機能を一時的に無効にする（ファイル内容のテキストや画像を挿入していく操作が変更と判定されてしまうため）
        
        #読み込んだ要素を順に処理
        for item in loaded_data["content"]:
            #テキストの場合
            if item["type"] == "text":
                main_memo.insert(tk.END, item["content"])
            #画像の場合
            elif item["type"] == "image":
                image_path = item["path"]#画像のパスを取得

                #画像ファイルが存在する場合
                if os.path.exists(image_path):
                    original_image = Image.open(image_path)#画像を開く
                    
                    #画像サイズ変更
                    width = PICTURE_WIDTH
                    height = int(original_image.height * width / original_image.width)
                    resized_image = original_image.resize((width, height), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(resized_image)#画像をPhotoImageに変換

                    #画像を挿入し、画像名を取得
                    image_name = main_memo.image_create(tk.INSERT, image=photo)
                    #画像名をキーにしてパスとPhotoImageを保持
                    inserted_images[image_name] = {"photo": photo, "path": image_path}


                    main_memo.tag_add(image_name, f"insert-1c")#image_nameをこのインデックスに追加
                    main_memo.tag_bind(image_name, "<Button-1>", lambda event, img_path=filepath,img_name=image_name: on_image_click(event, img_path, img_name))#左クリック
                    main_memo.tag_bind(image_name, "<Double-Button-1>", lambda event, img_path=image_path: show_image_popup(img_path))#ダブルクリック
                    main_memo.tag_bind(image_name, "<Button-3>", lambda event, img_name=image_name: show_image_context_menu(event, img_name))#右クリック
                    
                    main_memo.tag_bind(image_name, "<Enter>", lambda event: main_memo.config(cursor="hand2"))#カーソルが画像に入ったとき
                    main_memo.tag_bind(image_name, "<Leave>", lambda event: main_memo.config(cursor="xterm"))#カーソルが画像から出たとき
                
                else:
                    main_memo.insert(tk.END, f"[画像が見つかりません: {os.path.basename(image_path)}]")
        
        
        main_memo.config(undo=True)#Undo機能を再度有効にする
        main_memo.edit_separator()#Undoスタックの区切りを設定

        #末尾の余計な改行を削除（ファイルを開くたびに改行が含まれてしまうため）
        content_after_load = main_memo.get("1.0", tk.END)
        if content_after_load.endswith('\n\n'):
            main_memo.delete("end-2c", tk.END)
        
        main_memo.focus_set()#カーソルを自動でセット
        modified = False#編集状態をリセット
        main_memo.update_idletasks() 
        main_memo.edit_modified(False)#Tkinterのmodifiedフラグもリセット

        current_filepath = filepath
        form.title(os.path.basename(filepath))
        print("読み込み完了", "ファイルが正常に読み込まれました。")

    except Exception as e:
        print("エラー", f"ファイルの読み込み中にエラーが発生しました: {e}")

def save_file(overwrite=False):
    """ファイルを保存"""
    global current_filepath

    #上書き保存か名前を付けて保存（current_filepathの中身が存在しているかどうか）
    if overwrite and current_filepath:
        #上書き保存
        filepath = current_filepath
    else:
        #名前を付けて保存
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not filepath:
            return
        
        current_filepath = filepath
    
    try:
        data_to_save = []

        #ファイルの最初から最後まで
        start_index = "1.0"
        end_index = main_memo.index(tk.END)

        dump = main_memo.dump(start_index, end_index, image=True, text=True)#ファイル内容をすべて取得
        for i in range(len(dump)):
            tag = dump[i][0]
            
            #テキストの場合
            if tag == "text":
                text = dump[i][1]
                if text:
                    data_to_save.append({"type": "text", "content": text})
            #画像の場合
            elif tag == "image":
                image_name = dump[i][1]
                image_info = inserted_images.get(image_name)
                if image_info and "path" in image_info:
                    data_to_save.append({"type": "image", "path": image_info["path"]})
                else:
                    messagebox.showwarning("警告", f"画像情報が見つかりません: {image_name}")

        full_data_to_save = {
            "font_size": selected_font_size.get(),#現在のフォントサイズ
            "content": data_to_save#実際のメモ内容
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(full_data_to_save, f, indent=4)#JSON形式で保存

        print("保存完了", "ファイルが正常に保存されました。")

        form.title(os.path.basename(filepath))
        modified = False#ファイル内容変更フラグOFF
        main_memo.edit_modified(False)#Tkinterのmodifiedフラグもリセット

    except Exception as e:
        print("エラー", f"ファイルの保存中にエラーが発生しました: {e}")

def put_one_back():
    """操作を1つ戻す"""
    try:
        main_memo.edit_undo()
    except tk.TclError:
        print("警告", "これ以上戻すことができません。")

def put_one_forward():
    """操作を1つ進める"""
    try:
        main_memo.edit_redo()
    except tk.TclError:
        print("警告", "これ以上進めることができません。")

def func_modified(event=None):
    """main_memoの編集状態が変更されたときに呼び出される関数"""
    global modified
    is_tk_modified = main_memo.edit_modified()
    
    if is_tk_modified:
        #Tkinterが変更済みと判断した場合、ファイル内容変更フラグON
        modified = True
    else:
        #Tkinterが未変更と判断した場合、ファイル内容変更フラグOFF
        modified = False

def on_closing():
    """アプリケーションを閉じる前に確認"""
    global modified

    if modified:#ファイル内容が変更されていた場合
        result = messagebox.askyesnocancel("確認", "変更内容を保存しますか？")
        if result is None:#キャンセルが選択された場合
            return
        elif result:#はいが選択された場合
            save_file(overwrite=True)
    form.destroy()#アプリケーションを終了

def change_font_size(size):
    """メインメモのフォントサイズを変更する"""
    current_font = main_memo.cget("font")#現在のフォント設定を取得
    font_parts = current_font.rsplit(" ", 1)#フォント名とサイズを分割
    font_name = font_parts[0] if len(font_parts) > 1 else "Consolas"#デフォルトフォント

    main_memo.config(font=(font_name, size))#フォントサイズを変更
    selected_font_size.set(size)

def on_main_memo_click(event):
    """テキストがクリックされたときの処理"""
    global selected_image_name_for_highlight

    #クリックされた場所が画像の上かどうかを判断
    click_point = main_memo.tag_names(f"@{event.x},{event.y}")#クリックした場所にあるタグを探す

    #現在ハイライトされている画像がある場合
    if selected_image_name_for_highlight:
        #もしクリックされた位置に、現在ハイライトされている画像のタグが含まれていなければ、ハイライトを解除
        if selected_image_name_for_highlight not in click_point:
            apply_image_highlight(selected_image_name_for_highlight, False)
            selected_image_name_for_highlight = None
            main_memo.config(cursor="xterm")

#文字列編集系
def cut_text():
    """テキストを切り取り"""
    main_memo.event_generate("<<Cut>>")
    modified=True#ファイル内容変更フラグON

def copy_text():
    """テキストをコピー"""
    main_memo.event_generate("<<Copy>>")
    modified=True#ファイル内容変更フラグON

def paste_text():
    """テキストを貼り付け"""
    main_memo.event_generate("<<Paste>>")
    modified=True#ファイル内容変更フラグON

#画像系
def insert_image():
    """画像を挿入"""
    global inserted_images

    filepath=filedialog.askopenfilename(
        title="画像を選択してください",
        filetypes=[("Image files","*.png *.jpg *.jpeg *.bmp")]
    )

    if not filepath:
        return

    try:
        #現在のカーソル位置の直前の文字を確認
        current_index = main_memo.index(tk.INSERT)
        if current_index != "1.0" and main_memo.get(f"{current_index}-1c", current_index) == "\t":
            #カーソルがタブの直後にある場合、そのタブを削除
            main_memo.delete(f"{current_index}-1c", current_index)


        original_image=Image.open(filepath)

        #画像のサイズ変更
        width=PICTURE_WIDTH#横幅固定
        height=int(original_image.height * width / original_image.width)#縦幅を合わせる（画像によって変わる）
        resized_image=original_image.resize((width,height),Image.Resampling.LANCZOS)

        photo=ImageTk.PhotoImage(resized_image)
        # 画像を挿入し、画像名を取得
        image_name = main_memo.image_create(tk.INSERT, image=photo)
        # 画像名をキーにしてパスとPhotoImageを保持
        inserted_images[image_name] = {"photo": photo, "path": filepath}

        # 画像クリックイベントをバインド
        main_memo.tag_add(image_name, f"insert-1c")
        main_memo.tag_bind(image_name, "<Button-1>", lambda event, img_path=filepath,img_name=image_name: on_image_click(event, img_path, img_name))#左クリック
        main_memo.tag_bind(image_name, "<Double-Button-1>", lambda event, img_path=filepath: show_image_popup(img_path))#ダブルクリック
        main_memo.tag_bind(image_name, "<Button-3>", lambda event, img_name=image_name: show_image_context_menu(event, img_name))#右クリック

        main_memo.tag_bind(image_name, "<Enter>", lambda event: main_memo.config(cursor="hand2"))#カーソルが画像に入ったとき
        main_memo.tag_bind(image_name, "<Leave>", lambda event: main_memo.config(cursor="xterm"))#カーソルが画像から出たとき

        modified=True#ファイル内容変更フラグON

    except Exception as e:
        messagebox.showerror("エラー", f"画像ファイルの読み込み中にエラーが発生しました: {e}")

def show_image_popup(img_path):
    """画像を別ウィンドウで拡大表示"""
    try:
        popup = tk.Toplevel(form)
        popup.title("画像の拡大表示")

        popup.focus_set()#このウィンドウにフォーカスを設定

        popup.resizable(False,False)  #ウィンドウのサイズ変更を禁止

        popup.bind("<FocusOut>", lambda event: popup_close(popup))#このウィンドウからフォーカスが外れたときウィンドウを閉じる
        popup.protocol("WM_DELETE_WINDOW", lambda: popup_close(popup))
        
        img = Image.open(img_path)  # 画像のパスを指定して画像を開く

        max_width, max_height = 800, 600#最大サイズ
        width, height = img.size#画像のサイズ取得

        scale = min(max_width / width, max_height / height, 1.0)
        if scale < 1.0:
            img = img.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(img)

        label = tk.Label(popup, image=photo)
        label.image = photo  #参照保持
        label.pack()


        #ポップアップウィンドウの位置を親ウィンドウの中央に配置
        popup.update_idletasks()
            
        x = form.winfo_x() + (form.winfo_width() // 2) - (popup.winfo_width() // 2)   #元ウィンドウのx座標 + 元ウィンドウの幅の半分 - ポップアップの幅の半分
        y = form.winfo_y() + (form.winfo_height() // 2) - (popup.winfo_height() // 2) #元ウィンドウのy座標 + 元ウィンドウの高さの半分 - ポップアップの高さの半分

        popup.geometry(f"+{x}+{y}") #位置設定

    except Exception as e:
        messagebox.showerror("エラー", f"画像の拡大表示に失敗しました: {e}")

def popup_close(popup_window):
    """ポップアップウィンドウが閉じられたときにグローバル変数をクリアし、Text選択を解除する"""
    global current_popup_photo, current_original_image, current_image_label, current_popup_window, selected_image_name_for_highlight
    
    if popup_window and popup_window.winfo_exists():
        popup_window.destroy()
        
    #グローバル変数クリア
    current_popup_photo = None
    current_original_image = None
    current_image_label = None
    current_popup_window = None

    #画像ハイライトが表示されていた場合、解除する
    if selected_image_name_for_highlight:
        apply_image_highlight(selected_image_name_for_highlight, False)
        selected_image_name_for_highlight = None

    #ここでTextウィジェットの選択範囲をクリア
    main_memo.tag_remove(tk.SEL, "1.0", tk.END)

def show_image_context_menu(event, image_name):
    """画像を右クリックしたときに表示されるコンテキストメニュー"""
    context_menu = tk.Menu(form, tearoff=0)
    context_menu.add_command(label="画像の拡大表示", command=lambda: show_image_popup(inserted_images[image_name]['path']))
    context_menu.add_command(label="画像を削除", command=lambda: delete_image(image_name))
    context_menu.post(event.x_root, event.y_root)

def delete_image(image_name):
    """画像を削除する関数"""
    global selected_image_name_for_highlight

    if image_name in inserted_images:
        ranges = main_memo.tag_ranges(image_name)
        
        #タグが適用されている範囲が見つかった場合
        if ranges:
            start_index = ranges[0]#範囲の開始インデックス
            end_index = ranges[1]
            
            main_memo.delete(start_index, end_index)#タグの範囲で削除
        else:
            print(f"警告: 画像 '{image_name}' に関連付けられたテキスト範囲が見つかりませんでした。")
            return

        #inserted_imagesから削除
        del inserted_images[image_name]

    else:
        print(f"警告: 画像 '{image_name}' は認識されませんでした。")
        return

    # 削除された画像がハイライトされていたら、リセット
    if selected_image_name_for_highlight == image_name:
        selected_image_name_for_highlight = None

    print(f"画像 '{image_name}' が削除されました。")

def delete_selected_image(selected_image_name):
    """選択された画像を削除する関数"""
    if selected_image_name:
        delete_image(selected_image_name)
    else:
        messagebox.showinfo("情報", "削除する画像が選択されていません。")

def on_image_click(event, img_path, img_name):
    """画像がクリックされたときの処理（ハイライト切り替えを含む）"""
    global selected_image_name_for_highlight

    #現在ハイライトされている画像があれば、ハイライトを解除
    if selected_image_name_for_highlight:
        apply_image_highlight(selected_image_name_for_highlight, False)

    #クリックされた画像が既に選択されていたか、新しい画像かを確認
    if selected_image_name_for_highlight == img_name:
        #同じ画像の場合は、選択解除
        selected_image_name_for_highlight = None
    else:
        #新しい画像にハイライトを適用
        selected_image_name_for_highlight = img_name
        apply_image_highlight(selected_image_name_for_highlight, True)

def apply_image_highlight(image_name, highlight_on):
    """画像にハイライトを適用または解除する関数"""
    #画像が挿入されているか確認
    if image_name not in inserted_images:
        return

    img_info = inserted_images[image_name]
    original_pil_image = img_info.get("original_pil_image")
    image_path = img_info.get("path")

    if original_pil_image is None:
        #オリジナルPIL画像が保存されていない場合は再読み込み
        try:
            original_pil_image = Image.open(image_path)
            inserted_images[image_name]["original_pil_image"] = original_pil_image
        except Exception as e:
            print(f"オリジナル画像の再読み込みに失敗しました: {e}")
            return

    #現在の表示サイズを取得（挿入時のリサイズしたサイズ）
    #Textウィジェットから直接取得できないため、挿入時のwidthを再利用
    display_width = PICTURE_WIDTH
    display_height = int(original_pil_image.height * display_width / original_pil_image.width)
    
    if highlight_on:
        #画像をリサイズしてから透明度を調整
        temp_image = original_pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        
        #明るさを調整 (ImageEnhance.Brightness を使用)
        enhancer = ImageEnhance.Brightness(temp_image)
        brightened_image = enhancer.enhance(HIGHLIGHT_BRIGHTNESS_FACTOR)

        #画像にアルファチャンネルがない場合は追加
        if brightened_image.mode != 'RGBA':
            brightened_image = brightened_image.convert('RGBA')
        
        #画像の色を薄く見せる
        alpha = int(255 * HIGHLIGHT_OPACITY_FACTOR)#不透明度を設定
        white_layer = Image.new('RGBA', brightened_image.size, (255, 255, 255, 255 - alpha))#透明度に応じて白を重ねる
        
        #blend関数で合成 (画像と白いレイヤーを混ぜる)
        #alphaが1.0だと全て画像、0.0だと全て白レイヤーになる
        blended_image = Image.blend(brightened_image, white_layer, alpha=(1.0 - HIGHLIGHT_OPACITY_FACTOR))
        
        final_image = blended_image
        
    else:
        #ハイライト解除時は元の画像（リサイズ済み）に戻す
        final_image = original_pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)

    new_photo = ImageTk.PhotoImage(final_image)#画像を適用

    #Textウィジェットの画像アイテムを更新
    main_memo.image_configure(image_name, image=new_photo)
    inserted_images[image_name]["photo"] = new_photo#PhotoImage参照を更新

#ヘルプメッセージ系
def show_about():
    """アプリ情報を表示"""
    messagebox.showinfo(
        "ピクメモについて",
        "画像を挿入できるメモ帳アプリケーションです。\n"
        "Python と tkinter で作成しました。\n"
    )

def show_how_to_use():
    """使い方を表示"""
    messagebox.showinfo(
        "ショートカットキー",
        "各ボタンに書いてあるキーをCtrlキーと一緒に押すことで、\n"
        "同じ操作を行うことができます。"
        "\n\n"
        "新規作成: \tCtrl + N\n"
        "開く: \t\tCtrl + P\n"
        "上書き保存: \tCtrl + S\n"
        "画像挿入: \tCtrl + I\n"
        "一つ戻す: \t\tCtrl + Z\n"
        "一つ進める: \tCtrl + Y\n"
        "終了: \t\tCtrl + Q\n"
    )

def show_version():
    """バージョン情報を表示"""
    messagebox.showinfo(
        "バージョン情報",
        "バージョン:\t1.0.2\n"
        "更新日:\t2025/07/27\n"
    )

#文字設定系
def change_font_color():
    """選択したテキストの色を変更する関数"""
    color_code = None

    color_tuple = colorchooser.askcolor(title="文字色を選択")
    if color_tuple:
        color_code = color_tuple[1]

    if color_code:
        try:
            start_index = main_memo.index(tk.SEL_FIRST)
            end_index = main_memo.index(tk.SEL_LAST)

            main_memo.tag_remove("colored", "1.0", tk.END)

            main_memo.tag_configure("colored", foreground=color_code)
            main_memo.tag_add("colored", start_index, end_index)
        except tk.TclError:
            #選択範囲がない場合デフォルトカラーを変更する
            main_memo.config(foreground=color_code)
            main_memo.edit_modified(True)

        


#---GUI---
form=tk.Tk()#tk作成
form.title("ピクメモ")
form.minsize(1000,560)
form.protocol("WM_DELETE_WINDOW", on_closing)

selected_font_size = tk.IntVar()# フォントサイズを保持する変数
selected_font_size.set(12)  # 初期フォントサイズを12ptに設定

#メニューバーの作成
menubar=Menu(form)
form.config(menu=menubar)

#ファイルメニュー
file_menu=Menu(menubar,tearoff=0)
menubar.add_cascade(label="ファイル",menu=file_menu)
file_menu.add_command(label="新規作成(N)", command=new_file)
file_menu.add_command(label="開く(P)", command=open_file)
file_menu.add_command(label="名前を付けて保存(S)", command=lambda: save_file(overwrite=False))
file_menu.add_command(label="上書き保存(S)", command=lambda: save_file(overwrite=True))
file_menu.add_separator()  # 区切り線
file_menu.add_command(label="終了(Q)", command=on_closing)

#編集メニュー
edit_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="編集", menu=edit_menu)
edit_menu.add_command(label="切り取り(X)", command=cut_text)
edit_menu.add_command(label="コピー(C)", command=copy_text)
edit_menu.add_command(label="貼り付け(V)", command=paste_text)
edit_menu.add_command(label="画像挿入(I)", command=insert_image)
edit_menu.add_separator()  # 区切り線
edit_menu.add_command(label="一つ戻す(Z)", command=put_one_back)
edit_menu.add_command(label="一つ進める(Y)", command=put_one_forward)

#画像メニュー
image_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="画像", menu=image_menu)
image_menu.add_command(label="画像挿入(I)", command=insert_image)
image_menu.add_command(label="画像を削除", command=lambda: delete_selected_image(selected_image_name_for_highlight))

#設定メニュー
settings_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="設定", menu=settings_menu)
font_menu = Menu(settings_menu, tearoff=0)
settings_menu.add_cascade(label="フォント設定", menu=font_menu)
font_menu.add_radiobutton(label="小 (10pt)", command=lambda: change_font_size(10), variable=selected_font_size, value=10)
font_menu.add_radiobutton(label="中 (12pt)", command=lambda: change_font_size(12), variable=selected_font_size, value=12)
font_menu.add_radiobutton(label="大 (14pt)", command=lambda: change_font_size(14), variable=selected_font_size, value=14)
font_menu.add_radiobutton(label="特大 (16pt)", command=lambda: change_font_size(16), variable=selected_font_size, value=16)
font_menu.add_radiobutton(label="特特大 (18pt)", command=lambda: change_font_size(18), variable=selected_font_size, value=18)
settings_menu.add_command(label="テーマ設定", command=lambda: messagebox.showinfo("テーマ設定", "テーマ設定の機能はまだ実装されていません。"))

#ヘルプメニュー
help_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="ヘルプ", menu=help_menu)
help_menu.add_command(label="ピクメモについて", command=show_about)
help_menu.add_command(label="ショートカットキー", command=show_how_to_use)
help_menu.add_command(label="バージョン情報", command=show_version)

#フォントごとの設定
menubar.add_command(label="文字色", command=change_font_color)

#ショートカットキー設定
form.bind('<Control-n>', lambda event: new_file())
form.bind('<Control-p>', lambda event: open_file())
form.bind('<Control-s>', lambda event: save_file(overwrite=True))
form.bind('<Control-i>', lambda event: insert_image())
form.bind('<Control-z>', lambda event: put_one_back())
form.bind('<Control-y>', lambda event: put_one_forward())
form.bind('<Control-q>', lambda event: on_closing())
form.bind('<Control-d>', lambda event: delete_selected_image(selected_image_name_for_highlight))

#
text_frame = tk.Frame(form)
text_frame.pack(expand=True, fill='both')

#テキスト画面を表示させる
main_memo = tk.Text(text_frame, bg="white", fg="black", wrap=tk.WORD, font=("Consolas", selected_font_size.get()), undo=True)
main_memo.pack(side='left', expand=True, fill='both')

scrollbar = tk.Scrollbar(text_frame, command=main_memo.yview)
scrollbar.pack(side='right', fill='y')
main_memo.config(yscrollcommand=scrollbar.set)

main_memo.bind('<<Modified>>', func_modified)#main_memoの編集状態が変更されたとき
main_memo.bind("<Button-1>", on_main_memo_click)#main_memoのテキストをクリックしたとき
main_memo.focus_set()#カーソルを自動でセット


#ウィンドウを中央に配置
form.update_idletasks()

x = (form.winfo_screenwidth() // 2) - (form.winfo_width() // 2)   #(画面の幅 // 2) - (ウィンドウの幅 // 2)
y = (form.winfo_screenheight() // 2) - (form.winfo_height() // 2) #(画面の高さ // 2) - (ウィンドウの高さ // 2)

form.geometry(f"+{x}+{y}")


form.mainloop()#実行