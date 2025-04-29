import tkinter as tk
from tkinter import ttk
import json
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

class FaturaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Market - Sistema de Faturas")
        self.root.geometry("1000x600")

        # Carregar produtos do arquivo JSON
        with open('produtos.json', 'r', encoding='utf-8') as file:
            self.produtos = json.load(file)

        # Carrinho de compras
        self.carrinho = []

        self.setup_gui()

    def setup_gui(self):
        # Frame principal dividido em duas colunas
        self.main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Coluna esquerda - Lista de produtos
        self.produtos_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.produtos_frame)

        # Notebook para categorias
        self.notebook = ttk.Notebook(self.produtos_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Criar abas para cada categoria
        self.category_frames = {}
        for categoria in self.produtos.keys():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=categoria)
            self.category_frames[categoria] = frame
            self.criar_lista_produtos(categoria, frame)

        # Coluna direita - Carrinho
        self.carrinho_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.carrinho_frame)

        # Lista do carrinho
        self.carrinho_label = ttk.Label(self.carrinho_frame, text="Carrinho de Compras", font=("Arial", 12, "bold"))
        self.carrinho_label.pack(pady=5)

        self.carrinho_tree = ttk.Treeview(self.carrinho_frame, columns=("nome", "preco"), show="headings")
        self.carrinho_tree.heading("nome", text="Produto")
        self.carrinho_tree.heading("preco", text="Preço")
        self.carrinho_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Botão remover item
        self.btn_remover = ttk.Button(self.carrinho_frame, text="Remover Item", command=self.remover_item)
        self.btn_remover.pack(pady=5)

        # Botão finalizar compra
        self.btn_finalizar = ttk.Button(self.carrinho_frame, text="Finalizar Compra", command=self.finalizar_compra)
        self.btn_finalizar.pack(pady=5)

        # Total
        self.total_label = ttk.Label(self.carrinho_frame, text="Total: €0.00", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=5)

    def criar_lista_produtos(self, categoria, frame):
        tree = ttk.Treeview(frame, columns=("nome", "preco"), show="headings")
        tree.heading("nome", text="Produto")
        tree.heading("preco", text="Preço")
        tree.pack(fill=tk.BOTH, expand=True)

        for produto in self.produtos[categoria]:
            tree.insert("", tk.END, values=(produto["nome"], f"€{produto['preco']:.2f}"))

        tree.bind("<Double-1>", lambda event, cat=categoria: self.adicionar_ao_carrinho(event, cat))

    def adicionar_ao_carrinho(self, event, categoria):
        tree = event.widget
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0])
            produto_nome = item['values'][0]
            for produto in self.produtos[categoria]:
                if produto['nome'] == produto_nome:
                    self.carrinho.append({**produto, 'categoria': categoria})
                    self.carrinho_tree.insert("", tk.END, values=(produto['nome'], f"€{produto['preco']:.2f}"))
                    self.atualizar_total()
                    break

    def remover_item(self):
        selection = self.carrinho_tree.selection()
        if selection:
            item = self.carrinho_tree.item(selection[0])
            produto_nome = item['values'][0]
            self.carrinho = [p for p in self.carrinho if p['nome'] != produto_nome]
            self.carrinho_tree.delete(selection[0])
            self.atualizar_total()

    def atualizar_total(self):
        total = sum(item['preco'] for item in self.carrinho)
        self.total_label.config(text=f"Total: €{total:.2f}")

    def finalizar_compra(self):
        if not self.carrinho:
            return

        # Gerar PDF
        filename = f"fatura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.gerar_pdf(filename)

        # Limpar carrinho
        self.carrinho = []
        for item in self.carrinho_tree.get_children():
            self.carrinho_tree.delete(item)
        self.atualizar_total()

    def gerar_pdf(self, filename):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        # Cabeçalho
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Mini Market")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        c.drawString(50, height - 90, "NIF: 123456789")

        # Produtos
        y = height - 120
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Produtos")
        y -= 20

        total = 0
        total_iva = {0: 0, 6: 0, 23: 0}
        total_desconto = 0
        valor_liquido = {0: 0, 6: 0, 23: 0}

        for item in self.carrinho:
            c.setFont("Helvetica", 10)
            preco_base = item['preco']
            desconto = item['desconto']
            iva_rate = int(item['iva'] * 100)
            
            valor_desconto = preco_base * desconto
            preco_com_desconto = preco_base - valor_desconto
            valor_iva = preco_com_desconto * item['iva']
            
            total_desconto += valor_desconto
            total_iva[iva_rate] += valor_iva
            valor_liquido[iva_rate] += preco_com_desconto
            
            # Mostrar produto e preço
            c.drawString(50, y, item['nome'])
            c.drawString(300, y, f"€{preco_base:.2f}")
            if desconto > 0:
                c.drawString(370, y, f"-€{valor_desconto:.2f}")
            c.drawString(440, y, f"IVA {iva_rate}%")
            y -= 15

        y -= 20
        # Resumo IVA
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Resumo IVA")
        y -= 15

        for taxa in [0, 6, 23]:
            if valor_liquido[taxa] > 0:
                c.setFont("Helvetica", 10)
                c.drawString(50, y, f"Taxa {taxa}%")
                c.drawString(150, y, f"Base: €{valor_liquido[taxa]:.2f}")
                c.drawString(300, y, f"IVA: €{total_iva[taxa]:.2f}")
                c.drawString(400, y, f"Total: €{(valor_liquido[taxa] + total_iva[taxa]):.2f}")
                y -= 15

        # Total e Descontos
        y -= 20
        total = sum(valor_liquido.values()) + sum(total_iva.values())
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Total Descontos:")
        c.drawString(400, y, f"€{total_desconto:.2f}")
        y -= 20
        
        c.drawString(50, y, "Total a Pagar:")
        c.drawString(400, y, f"€{total:.2f}")

        c.save()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaturaApp(root)
    root.mainloop()