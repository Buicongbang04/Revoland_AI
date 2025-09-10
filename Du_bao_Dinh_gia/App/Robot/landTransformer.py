import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 10000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe, persistent=False)

    def forward(self, x):
        return x + self.pe[:, : x.size(1)]  # type: ignore


class TokenEmbedding1D(nn.Module):
    def __init__(self, c_in: int, d_model: int, kernel_size: int = 3):
        super().__init__()
        padding = (kernel_size - 1) // 2
        self.conv = nn.Conv1d(
            in_channels=c_in,
            out_channels=d_model,
            kernel_size=kernel_size,
            padding=padding,
            padding_mode="circular",
        )
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x):
        # x: [B, T, F]
        x = x.transpose(1, 2)  # [B, F, T]
        y = self.conv(x)  # [B, D, T]
        y = y.transpose(1, 2)  # [B, T, D]
        return self.norm(y)


class EncoderBlock(nn.Module):
    def __init__(
        self, d_model: int, nhead: int, dim_ff: int = 512, dropout: float = 0.1
    ):
        super().__init__()
        self.attn = nn.MultiheadAttention(
            d_model, nhead, dropout=dropout, batch_first=True
        )
        self.ln1 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, dim_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim_ff, d_model),
        )
        self.ln2 = nn.LayerNorm(d_model)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        h, _ = self.attn(x, x, x)
        x = x + self.drop(h)
        x = self.ln1(x)
        h = self.ff(x)
        x = x + self.drop(h)
        x = self.ln2(x)
        return x


class Stockformer(nn.Module):
    def __init__(
        self,
        num_features: int,
        num_phuong: int,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 3,
        dim_ff: int = 512,
        dropout: float = 0.1,
        output_len: int = 3,
        phuong_emb_dim: int = 16,
    ):
        super().__init__()
        # Embedding cho Phuong
        self.phuong_emb = nn.Embedding(num_phuong, phuong_emb_dim)

        # Embedding cho input features
        self.embed = TokenEmbedding1D(num_features + phuong_emb_dim, d_model)
        self.posenc = SinusoidalPositionalEncoding(d_model)

        # Encoder stack
        self.encoder = nn.ModuleList(
            [EncoderBlock(d_model, nhead, dim_ff, dropout) for _ in range(num_layers)]
        )

        # Head: dự báo multi-step
        self.head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, output_len),
        )

    def forward(self, x_num, phuong_idx):
        """
        x_num: [B, T, F]   numeric features
        phuong_idx: [B]    index của phường (int)
        """
        B, T, _ = x_num.size()
        emb = self.phuong_emb(phuong_idx)  # [B, Demb]
        emb = emb.unsqueeze(1).expand(-1, T, -1)  # [B, T, Demb]
        x = torch.cat([x_num, emb], dim=-1)  # [B, T, F + Demb]

        x = self.embed(x)
        x = self.posenc(x)
        for blk in self.encoder:
            x = blk(x)

        last = x[:, -1, :]  # lấy token cuối cùng
        out = self.head(last)  # [B, output_len]
        return out
