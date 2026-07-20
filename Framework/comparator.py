import torch

class Comparator:
    """
    INPUT:
        sub_windows: List[torch.Tensor]
    OUTPUT:
        distances / threshold
    """

    def __init__(self, model, optimizer, sampler, device,
                 epochs, sub_window_num, n, k,
                 eps_small, eps_big, temperature,
                 lamb, percentile):

        self.model = model
        self.optimizer = optimizer
        self.sampler = sampler
        self.device = device

        self.epochs = epochs
        self.sub_window_num = sub_window_num
        self.n = n
        self.k = k
        self.eps_small = eps_small
        self.eps_big = eps_big
        self.temperature = temperature
        self.lamb = lamb
        self.percentile = percentile

        self.model.train()

        for param in self.model.parameters():
            param.requires_grad = True

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.0)

    # ---------------- SAMPLING ----------------
    def generate_samples(self, sub_win):
        return self.sampler.sample(sub_win)

    # ---------------- DISTANCES ----------------
    def compute_positive_loss(self, emb):
        diff = emb.unsqueeze(1) - emb.unsqueeze(0)
        dist = torch.norm(diff, dim=2)
        mask = torch.triu(torch.ones_like(dist), diagonal=1).bool()
        return dist[mask].mean(), dist[mask]

    def compute_negative_loss(self, a, b):
        diff = a.unsqueeze(1) - b.unsqueeze(0)
        dist = torch.norm(diff, dim=2)
        mask = torch.eye(dist.size(0), device=dist.device).bool()
        return dist[~mask].mean()

    def contrastive_loss(self, pos, neg):
        #pos = torch.exp(torch.stack(pos) / self.temperature)
        #neg = torch.exp(torch.stack(neg) / self.temperature)

        #return torch.log(torch.sum(pos) / (torch.sum(pos) + torch.sum(neg)))
        pos = torch.stack(pos)
        neg = torch.stack(neg)

        pos = torch.clamp(pos, 0, 20)
        neg = torch.clamp(neg, 0, 20)

        pos_exp = torch.exp(pos / self.temperature)
        neg_exp = torch.exp(neg / self.temperature)

        loss = -torch.log((torch.sum(pos_exp) + 1e-8) / (torch.sum(pos_exp) + torch.sum(neg_exp) + 1e-8))

        #loss = torch.nan_to_num(loss, nan=0.0)

        return loss

    def gp(self, samples, output):
        grads = torch.autograd.grad(
            outputs=output,
            inputs=samples,
            grad_outputs=torch.ones_like(output),
            create_graph=True,
            retain_graph=True,
            only_inputs=True
        )[0]

        norm = torch.sqrt(torch.sum(grads ** 2, dim=1) + 1e-12)
        return ((norm - 1) ** 2).mean()

    # ---------------- TRAIN (IDENTICAL TO ORIGINAL) ----------------
    def train(self, window_data):
        windows = torch.split(
            window_data,
            int(window_data.size(0) / self.sub_window_num)
        )

        sub_samples = [self.generate_samples(w) for w in windows]

        for _ in range(self.epochs):

            pos_losses = []
            weak_neg_losses = []

            # ---------------- POS + WEAK NEG ----------------
            for samples in sub_samples:
                emb = self.model(samples).mean(dim=1)
                emb = torch.nn.functional.normalize(emb, p=2, dim=1)

                pos, _ = self.compute_positive_loss(emb)
                pos_losses.append(pos)

                unchanged = samples[:self.k // 2]
                altered = samples[self.k // 2:] + torch.normal(
                    0,
                    self.eps_small,
                    samples[self.k // 2:].shape
                ).to(self.device)

                e1 = self.model(unchanged).mean(dim=1)
                e2 = self.model(altered).mean(dim=1)

                weak_neg_losses.append(self.compute_negative_loss(e1, e2))

            # ---------------- STRONG NEG ----------------
            first = sub_samples[0]
            last = sub_samples[-1] + torch.normal(
                0,
                self.eps_big,
                sub_samples[-1].shape
            ).to(self.device)

            strong_neg = self.compute_negative_loss(
                self.model(first).mean(dim=1),
                self.model(last).mean(dim=1)
            )

            # ---------------- GP ----------------
            # (use last batch samples/embeddings as in original behaviour)
            gps = []

            for samples in sub_samples:
                emb = self.model(samples).mean(dim=1)
                gps.append(self.gp(samples, emb))

            gp = torch.mean(torch.stack(gps))

            # ---------------- TOTAL LOSS ----------------
            loss = self.contrastive_loss(
                pos_losses,
                weak_neg_losses + [strong_neg]
            ) + self.lamb * gp

            # ---------------- OPTIM STEP ----------------
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        return self.compute_threshold(windows)

    def test(self, window_data):
            windows = torch.split(
                window_data,
                int(window_data.size(0) / self.sub_window_num)
            )

            embs = []
            for w in windows:
                s = self.generate_samples(w)
                with torch.no_grad():
                    embs.append(self.model(s).mean(dim=1))

            pairwise = self.compute_all_pairwise_discrepancy(embs)
            consecutive = self.compute_consecutive_discrepancy(embs)

            return pairwise, consecutive    

    def compute_threshold(self, windows):
        losses = []

        for w in windows:
            s = self.generate_samples(w)
            emb = self.model(s).mean(dim=1)
            _, l = self.compute_positive_loss(emb)
            losses.append(l)

        return torch.quantile(torch.cat(losses), self.percentile)
    
    def compute_all_pairwise_discrepancy(self, embs):
        """
        embs: list of [N, d] tensors
        returns: matrix of pairwise discrepancies
        """
        distances = []

        for i in range(len(embs)):
            for j in range(i + 1, len(embs)):
                diff = embs[i].unsqueeze(1) - embs[j].unsqueeze(0)
                dist = torch.norm(diff, dim=2).mean()
                distances.append(dist)

        return torch.stack(distances)
    
    
    def compute_consecutive_discrepancy(self, embs):
        return torch.stack([
            self.compute_negative_loss(embs[i], embs[i + 1])
            for i in range(len(embs) - 1)
        ])
    
    