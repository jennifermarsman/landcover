import torch.nn as nn
import torch
from torch.nn import functional as F

#Few losses modified from: https://github.com/kevinzakka/pytorch-goodies/blob/master/losses.py

#crossentropy no one hot
class multiclass_ce(nn.modules.Module):
    def __init__(self):
        super(multiclass_ce, self).__init__()
        self.crossentropy = nn.CrossEntropyLoss()

    def __call__(self,y_true, y_pred):
        loss = self.crossentropy(y_pred, y_true)
        return loss

class multiclass_ce_points(nn.modules.Module):
    def __init__(self):
        super(multiclass_ce_points, self).__init__()
        self.crossentropy = nn.CrossEntropyLoss(ignore_index=0, reduction='mean')

    def __call__(self,y_true, y_pred):
        loss = self.crossentropy(y_pred, y_true)
        return loss

    
class weighted_ce_loss(nn.modules.Module):
    def __init__(self):
        super(weighted_ce_loss, self).__init__()

    def ce_loss(self, y_true, logits, weights, ignore=255):
        """Computes the weighted multi-class cross-entropy loss.
        Args:
            true: a tensor of shape [B, 1, H, W].
            logits: a tensor of shape [B, C, H, W]. Corresponds to
                the raw output or logits of the model.
            weight: a tensor of shape [C,]. The weights attributed
                to each class.
            ignore: the class index to ignore.
        Returns:
            weighted_ce_loss: the weighted multi-class cross-entropy loss.
        """
        ce_loss = F.cross_entropy(
            logits.float(),
            y_true.long(),
            ignore_index=ignore,
            weight=weights,
        )
        return ce_loss

    def __call__(self,y_true, logits, weights):
        ce = self.ce_loss(y_true, logits, weights)
        return ce

class multiclass_dice_loss(nn.modules.Module):
    def __init__(self):
        super(multiclass_dice_loss, self).__init__()

    def dice_loss(self, y_true, logits, eps=1e-7):
        """Computes the Sørensen–Dice loss.
        Note that PyTorch optimizers minimize a loss. In this
        case, we would like to maximize the dice loss so we
        return the negated dice loss.
        Args:
            y_true: a tensor of shape [B, 1, H, W].
            logits: a tensor of shape [B, C, H, W]. Corresponds to
                the raw output or logits of the model.
            eps: added to the denominator for numerical stability.
        Returns:
            dice_loss: the Sørensen–Dice loss.
        """
        num_classes = logits.shape[1]
        if num_classes == 1:
            true_1_hot = torch.eye(num_classes + 1)[y_true.squeeze(1)]
            true_1_hot = true_1_hot.permute(0, 3, 1, 2).float()
            true_1_hot_f = true_1_hot[:, 0:1, :, :]
            true_1_hot_s = true_1_hot[:, 1:2, :, :]
            true_1_hot = torch.cat([true_1_hot_s, true_1_hot_f], dim=1)
            pos_prob = torch.sigmoid(logits)
            neg_prob = 1 - pos_prob
            probas = torch.cat([pos_prob, neg_prob], dim=1)
        else:
            true_1_hot = torch.eye(num_classes)[y_true.squeeze(1)]
            true_1_hot = true_1_hot.permute(0, 3, 1, 2).float()
            probas = F.softmax(logits, dim=1)
        true_1_hot = true_1_hot.type(logits.type())
        dims = (0,) + tuple(range(2, y_true.ndimension()))
        intersection = torch.sum(probas * true_1_hot, dims)
        cardinality = torch.sum(probas + true_1_hot, dims)
        dice_loss = (2. * intersection / (cardinality + eps)).mean()
        return (1 - dice_loss)

    def __call__(self,y_true, logits):
        dice = self.dice_loss(y_true, logits)
        return dice

class multiclass_jaccard_loss(nn.modules.Module):
    def __init__(self):
        super(multiclass_jaccard_loss, self).__init__()

    def jaccard_loss(self, y_true, logits, eps=1e-7):
        """Computes the Jaccard loss, a.k.a the IoU loss.
        Note that PyTorch optimizers minimize a loss. In this
        case, we would like to maximize the jaccard loss so we
        return the negated jaccard loss.
        Args:
            y_true: a tensor of shape [B, H, W] or [B, 1, H, W].
            logits: a tensor of shape [B, C, H, W]. Corresponds to
                the raw output or logits of the model.
            eps: added to the denominator for numerical stability.
        Returns:
            jacc_loss: the Jaccard loss.
        """
        num_classes = logits.shape[1]
        if num_classes == 1:
            true_1_hot = torch.eye(num_classes + 1)[y_true.squeeze(1)]
            true_1_hot = true_1_hot.permute(0, 3, 1, 2).float()
            true_1_hot_f = true_1_hot[:, 0:1, :, :]
            true_1_hot_s = true_1_hot[:, 1:2, :, :]
            true_1_hot = torch.cat([true_1_hot_s, true_1_hot_f], dim=1)
            pos_prob = torch.sigmoid(logits)
            neg_prob = 1 - pos_prob
            probas = torch.cat([pos_prob, neg_prob], dim=1)
        else:
            true_1_hot = torch.eye(num_classes)[y_true.squeeze(1)]
            true_1_hot = true_1_hot.permute(0, 3, 1, 2).float()
            probas = F.softmax(logits, dim=1)
        true_1_hot = true_1_hot.type(logits.type())
        dims = (0,) + tuple(range(2, y_true.ndimension()))
        intersection = torch.sum(probas * true_1_hot, dims)
        cardinality = torch.sum(probas + true_1_hot, dims)
        union = cardinality - intersection
        jacc_loss = (intersection / (union + eps)).mean()
        return (1 - jacc_loss)

    def __call__(self,y_true, logits):
        jaccard = self.jaccard_loss(y_true, logits)
        return jaccard

class multiclass_tversky_loss(nn.modules.Module):
    def __init__(self):
        super(multiclass_tversky_loss, self).__init__()

    def tversky_loss(self, y_true, logits, alpha=0.5, beta=0.5, eps=1e-7):
        """Computes the Tversky loss [1].
        Args:
            y_true: a tensor of shape [B, H, W] or [B, 1, H, W].
            logits: a tensor of shape [B, C, H, W]. Corresponds to
                the raw output or logits of the model.
            alpha: controls the penalty for false positives.
            beta: controls the penalty for false negatives.
            eps: added to the denominator for numerical stability.
        Returns:
            tversky_loss: the Tversky loss.
        Notes:
            alpha = beta = 0.5 => dice coeff
            alpha = beta = 1 => tanimoto coeff
            alpha + beta = 1 => F beta coeff
        References:
            [1]: https://arxiv.org/abs/1706.05721
        """
        num_classes = logits.shape[1]
        if num_classes == 1:
            true_1_hot = torch.eye(num_classes + 1)[y_true.squeeze(1)]
            true_1_hot = true_1_hot.permute(0, 3, 1, 2).float()
            true_1_hot_f = true_1_hot[:, 0:1, :, :]
            true_1_hot_s = true_1_hot[:, 1:2, :, :]
            true_1_hot = torch.cat([true_1_hot_s, true_1_hot_f], dim=1)
            pos_prob = torch.sigmoid(logits)
            neg_prob = 1 - pos_prob
            probas = torch.cat([pos_prob, neg_prob], dim=1)
        else:
            true_1_hot = torch.eye(num_classes)[y_true.squeeze(1)]
            true_1_hot = true_1_hot.permute(0, 3, 1, 2).float()
            probas = F.softmax(logits, dim=1)
        true_1_hot = true_1_hot.type(logits.type())
        dims = (0,) + tuple(range(2, y_true.ndimension()))
        intersection = torch.sum(probas * true_1_hot, dims)
        fps = torch.sum(probas * (1 - true_1_hot), dims)
        fns = torch.sum((1 - probas) * true_1_hot, dims)
        num = intersection
        denom = intersection + (alpha * fps) + (beta * fns)
        tversky_loss = (num / (denom + eps)).mean()
        return (1 - tversky_loss)

    def __call__(self,y_true, logits, alpha, beta):
        tversky = self.tversky_loss(y_true, logits, alpha, beta)
        return tversky

#TODO: Test that this actually works
class super_resolution_loss(nn.modules.Module):
    def __init__(self, nlcd_class_weights, nlcd_means, nlcd_vars, boundary=0):
        super(super_resolution_loss, self).__init__()
        self.nlcd_class_weights = nlcd_class_weights
        self.nlcd_means = nlcd_means
        self.nlcd_vars = nlcd_vars
        self.boundary = boundary

    def ddist(self, prediction_mean, c_interval_center, c_interval_radius):
        return F.relu(torch.abs(prediction_mean - c_interval_center) - c_interval_radius)

    def super_res_loss(self, y_true, y_pred):
        super_res_crit = 0
        mask_size = torch.unsqueeze((torch.sum(y_true, dim=[1,2,3]) + 10), -1)

        for nlcd_idx in range(self.nlcd_class_weights[0]):
            c_mask = torch.unsqueeze(y_true[:,:,:,nlcd_idx], -1)
            c_mask_size = torch.sum(c_mask, dim=[1,2]) + 0.0000001

            c_interval_center = self.nlcd_means[nlcd_idx]
            c_interval_radius = self.nlcd_vars[nlcd_idx]

            masked_probs = y_pred * c_mask

            mean = torch.sum(masked_probs, dim=[1,2]) / c_mask_size
            var = torch.sum(masked_probs * (1. - masked_probs), dim=[1,2]) / (c_mask_size * c_mask_size)

            c_super_res_crit  = torch.sqrt(self.ddist(mean, c_interval_center, c_interval_radius))
            c_super_res_crit = c_super_res_crit / (
                        var + (c_interval_radius * c_interval_radius) + 0.000001)  # calculate denominator
            c_super_res_crit = c_super_res_crit + torch.log(var + 0.03)  # calculate log term
            c_super_res_crit = c_super_res_crit * (c_mask_size / mask_size) * self.nlcd_class_weights[
                nlcd_idx]  # weight by the fraction of NLCD pixels and the NLCD class weight
            super_res_crit = super_res_crit + c_super_res_crit  # accumulate

        super_res_crit = torch.sum(super_res_crit, dim=1)  # sum superres loss across highres classes
        return super_res_crit

