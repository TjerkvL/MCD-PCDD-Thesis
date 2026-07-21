# Imports
import torch


class Comparator:

    """
    INPUT:
        subWindows: list of [torch.Tensor]

    OUTPUT:
        distances / threshold
    """

    def __init__(
        self,
        model,
        optimizer,
        sampler,
        device,
        epochs,
        sub_window_num,
        n,
        k,
        eps_small,
        eps_big,
        temperature,
        lamb,
        percentile
    ):

        self.model = model
        self.optimizer = optimizer
        self.sampler = sampler
        self.device = device

        self.epochs = epochs
        self.subWindowNum = sub_window_num
        self.n = n
        self.k = k

        self.epsSmall = eps_small
        self.epsBig = eps_big

        self.temperature = temperature
        self.lamb = lamb
        self.percentile = percentile

        self.model.train()

        #for parameter in self.model.parameters():
        #    parameter.requires_grad = True

        #self.optimizer = torch.optim.Adam(
        #    self.model.parameters(),
        #    lr=0.0
        #)

    # Generate samples from a sub-window
    def generateSamples(self, subWindow):
        return self.sampler.sample(subWindow)

    # Calculate positive pair distances
    def computePositiveLoss(self, embeddings):

        difference = embeddings.unsqueeze(1) - embeddings.unsqueeze(0)
        distances = torch.norm(difference, dim=2)

        mask = torch.triu(torch.ones_like(distances), diagonal=1).bool()

        return distances[mask].mean(), distances[mask]

    # Calculate negative pair distances
    def computeNegativeLoss(self, embeddingA, embeddingB):

        difference = embeddingA.unsqueeze(1) - embeddingB.unsqueeze(0)
        distances = torch.norm(difference, dim=2)

        mask = torch.eye(distances.size(0), device=distances.device).bool()

        return distances[~mask].mean()

    # Contrastive loss calculation
    def contrastiveLoss(self, positiveLosses, negativeLosses):

        positiveLosses = torch.clamp(torch.stack(positiveLosses), 0, 20)
        negativeLosses = torch.clamp(torch.stack(negativeLosses), 0, 20)

        positiveExp = torch.exp(positiveLosses / self.temperature)
        negativeExp = torch.exp(negativeLosses / self.temperature)

        loss = -torch.log(
            (torch.sum(positiveExp) + 1e-8)
            /
            (torch.sum(positiveExp) + torch.sum(negativeExp) + 1e-8)
        )

        return loss

    # Gradient penalty calculation
    def computeGradientPenalty(self, samples, output):

        gradients = torch.autograd.grad(
            outputs=output,
            inputs=samples,
            grad_outputs=torch.ones_like(output),
            create_graph=True,
            retain_graph=True,
            only_inputs=True
        )[0]

        gradientNorm = torch.sqrt(torch.sum(gradients ** 2, dim=1) + 1e-12)

        return ((gradientNorm - 1) ** 2).mean()

    # Train encoder on window
    def train(self, windowData):

        subWindows = torch.split(windowData, int(windowData.size(0) / self.subWindowNum))

        subSamples = [
            self.generateSamples(window)
            for window in subWindows
        ]

        for _ in range(self.epochs):

            positiveLosses = []
            weakNegativeLosses = []

            # Positive pairs and weak negative pairs
            for samples in subSamples:

                embeddings = self.model(samples).mean(dim=1)
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

                positiveLoss, _ = self.computePositiveLoss(embeddings)
                positiveLosses.append(positiveLoss)

                unchangedSamples = samples[:self.k // 2]

                alteredSamples = samples[self.k // 2:] + torch.normal(
                    0,
                    self.epsSmall,
                    samples[self.k // 2:].shape
                ).to(self.device)

                unchangedEmbedding = self.model(unchangedSamples).mean(dim=1)
                alteredEmbedding = self.model(alteredSamples).mean(dim=1)

                weakNegativeLosses.append(
                    self.computeNegativeLoss(
                        unchangedEmbedding,
                        alteredEmbedding
                    )
                )

            # Strong negative pair
            firstSamples = subSamples[0]

            lastSamples = subSamples[-1] + torch.normal(
                0,
                self.epsBig,
                subSamples[-1].shape
            ).to(self.device)

            strongNegativeLoss = self.computeNegativeLoss(
                self.model(firstSamples).mean(dim=1),
                self.model(lastSamples).mean(dim=1)
            )

            # Gradient penalty
            gradientPenalties = []

            for samples in subSamples:

                embeddings = self.model(samples).mean(dim=1)

                gradientPenalties.append(
                    self.computeGradientPenalty(
                        samples,
                        embeddings
                    )
                )

            gradientPenalty = torch.mean(torch.stack(gradientPenalties))

            # Total loss
            loss = (
                self.contrastiveLoss(
                    positiveLosses,
                    weakNegativeLosses + [strongNegativeLoss]
                )
                +
                self.lamb * gradientPenalty
            )

            # Optimization step
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        return self.computeThreshold(subWindows)

    # Test discrepancy calculation
    def test(self, windowData):

        subWindows = torch.split(windowData, int(windowData.size(0) / self.subWindowNum))

        embeddings = []

        for window in subWindows:

            samples = self.generateSamples(window)

            with torch.no_grad():
                embeddings.append(
                    self.model(samples).mean(dim=1)
                )

        pairwiseDiscrepancy = self.computeAllPairwiseDiscrepancy(embeddings)

        consecutiveDiscrepancy = self.computeConsecutiveDiscrepancy(embeddings)

        return pairwiseDiscrepancy, consecutiveDiscrepancy


    # Compute threshold based on positive distances
    def computeThreshold(self, subWindows):

        losses = []

        for window in subWindows:

            samples = self.generateSamples(window)

            embeddings = self.model(samples).mean(dim=1)

            _, distances = self.computePositiveLoss(embeddings)

            losses.append(distances)

        return torch.quantile(
            torch.cat(losses),
            self.percentile
        )


    # Compute discrepancy between every sub-window pair
    def computeAllPairwiseDiscrepancy(self, embeddings):

        distances = []

        for i in range(len(embeddings)):

            for j in range(i + 1, len(embeddings)):

                difference = embeddings[i].unsqueeze(1) - embeddings[j].unsqueeze(0)

                distance = torch.norm(difference, dim=2).mean()

                distances.append(distance)

        return torch.stack(distances)


    # Compute discrepancy between consecutive windows
    def computeConsecutiveDiscrepancy(self, embeddings):

        return torch.stack(
            [
                self.computeNegativeLoss(
                    embeddings[i],
                    embeddings[i + 1]
                )
                for i in range(len(embeddings) - 1)
            ]
        )