import heapq
import pickle
from typing import List, Tuple

import numpy as np

from config import (
    FUSION_PATH_2020, LABELS_PATH_2020, IMAGE_IDS_PATH_2020, HJG_GRAPH_PATH_2020,
    FUSION_PATH_2019, LABELS_PATH_2019, IMAGE_IDS_PATH_2019, HJG_GRAPH_PATH_2019,
    CNN_DIM, ALPHA,
)


class SearchEngine:
    def __init__(self, fusion_path, labels_path, image_ids_path, hjg_path):
        self.vectors = np.load(fusion_path).astype(np.float32)
        self.labels = np.load(labels_path, allow_pickle=True)
        self.image_ids = np.load(image_ids_path, allow_pickle=True)

        self.cnn = self.vectors[:, :CNN_DIM]
        self.vit = self.vectors[:, CNN_DIM:]
        self.cnn /= (np.linalg.norm(self.cnn, axis=1, keepdims=True) + 1e-8)
        self.vit /= (np.linalg.norm(self.vit, axis=1, keepdims=True) + 1e-8)

        with open(hjg_path, "rb") as f:
            self.hjg = pickle.load(f)

    def d_euc(self, q, db):
        diff = db - q
        return np.einsum("ij,ij->i", diff, diff)

    def d_cos(self, q, db):
        return 1.0 - (db @ q)

    def search_hjg(self, q_vector: np.ndarray, top_k: int = 10, ef: int = 60) -> List[Tuple[float, int]]:
        q_cnn = q_vector[:CNN_DIM]
        q_vit = q_vector[CNN_DIM:]
        joint = self.hjg["joint"]
        coarse_idx = self.hjg["coarse_idx"]
        coarse = self.hjg["coarse"]

        def jd(idx):
            dc = float(np.sqrt(float(self.d_euc(q_cnn, self.cnn[idx:idx+1])[0])))
            dv = float(self.d_cos(q_vit, self.vit[idx:idx+1])[0])
            return ALPHA * dc + (1.0 - ALPHA) * dv

        start_local = int(np.random.randint(0, len(coarse_idx)))
        start_global = int(coarse_idx[start_local])
        visited_c = {start_local}
        best_d, best_g = jd(start_global), start_global
        heap_c = [(best_d, start_local, start_global)]

        while heap_c:
            d_cur, l_cur, g_cur = heapq.heappop(heap_c)
            if d_cur > best_d * 2.0:
                break
            for d_nb, g_nb in coarse[l_cur]:
                locs = np.where(coarse_idx == g_nb)[0]
                if len(locs) == 0:
                    continue
                l_nb = int(locs[0])
                if l_nb in visited_c:
                    continue
                visited_c.add(l_nb)
                d = jd(g_nb)
                if d < best_d:
                    best_d, best_g = d, g_nb
                heapq.heappush(heap_c, (d, l_nb, g_nb))

        visited_f = {best_g}
        d0 = jd(best_g)
        W, C = [(-d0, best_g)], [(d0, best_g)]

        while C:
            d_cur, n_cur = heapq.heappop(C)
            if len(W) >= ef and d_cur > -W[0][0]:
                break
            for d_nb, n_nb in joint[n_cur]:
                if n_nb in visited_f:
                    continue
                visited_f.add(n_nb)
                d = jd(n_nb)
                if len(W) < ef:
                    heapq.heappush(W, (-d, n_nb))
                    heapq.heappush(C, (d, n_nb))
                elif d < -W[0][0]:
                    heapq.heapreplace(W, (-d, n_nb))
                    heapq.heappush(C, (d, n_nb))

        results = sorted([(-nd, n) for nd, n in W])
        return results[:top_k]


engine_2020 = SearchEngine(FUSION_PATH_2020, LABELS_PATH_2020, IMAGE_IDS_PATH_2020, HJG_GRAPH_PATH_2020)
engine_2019 = SearchEngine(FUSION_PATH_2019, LABELS_PATH_2019, IMAGE_IDS_PATH_2019, HJG_GRAPH_PATH_2019)

ENGINES = {"isic2020": engine_2020, "isic2019": engine_2019}
