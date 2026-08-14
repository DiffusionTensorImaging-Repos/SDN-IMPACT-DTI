# Base-R port of permutation_one.R (no tidyverse; uses parallel::mclapply).
# Freedman-Lane cluster-extent permutation. Same model + logic as the original.
# Args: data_csv response_col metric_prefix out_dir base_label
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) >= 5)
data_csv <- args[1]; response_col <- args[2]; metric_prefix <- args[3]
out_dir <- args[4]; base <- args[5]

covariate_cols <- c("ICV", "Mean_tckstats", "Count_tckstats", "absolute_motion", "maternal_age")
alpha_node <- 0.05; alpha_fw <- 0.05
num_perm <- as.integer(Sys.getenv("R_PERM_N", unset = "5000"))
rng_seed <- 123
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

dat <- read.csv(data_csv, check.names = FALSE, stringsAsFactors = FALSE)
node_cols <- grep(paste0("^", metric_prefix, "[0-9]+$"), names(dat), value = TRUE)
if (length(node_cols) == 0) stop("No node columns for ", metric_prefix)
node_idx <- as.integer(sub(paste0("^", metric_prefix), "", node_cols))
o <- order(node_idx); node_cols <- node_cols[o]; node_idx <- node_idx[o]
num_nodes <- length(node_cols)

dat[[response_col]] <- as.numeric(dat[[response_col]])
for (cc in covariate_cols) dat[[cc]] <- as.numeric(dat[[cc]])
mask <- complete.cases(dat[, c(response_col, covariate_cols, node_cols)])
n_drop <- sum(!mask); dat <- dat[mask, , drop = FALSE]; n_subj <- nrow(dat)
if (n_subj < 5) { message("Fewer than 5 subjects — skipping ", base); quit(status = 0) }

y <- dat[[response_col]]
covdf <- dat[, covariate_cols, drop = FALSE]
full_formula <- as.formula(paste("y ~ node +", paste(covariate_cols, collapse = " + ")))
red_formula  <- as.formula(paste("y ~", paste(covariate_cols, collapse = " + ")))

fit_node <- function(yv, node, cov) {
  df0 <- data.frame(y = yv, node = node, cov); df0 <- df0[complete.cases(df0), ]
  if (nrow(df0) < 3 || sd(df0$node) == 0) return(c(Estimate = NA, t = NA, p = NA))
  fit <- lm(full_formula, data = df0); sm <- summary(fit)$coefficients
  if (!("node" %in% rownames(sm))) return(c(Estimate = NA, t = NA, p = NA))
  tv <- sm["node", "t value"]
  c(Estimate = sm["node", "Estimate"], t = tv, p = 2 * pt(-abs(tv), df = fit$df.residual))
}

set.seed(rng_seed)
ns <- t(sapply(node_cols, function(nc) fit_node(y, dat[[nc]], covdf)))
node_est <- ns[, "Estimate"]; node_t <- ns[, "t"]; node_p <- ns[, "p"]

clusters_from_sig <- function(sig, nodes) {
  if (!any(sig, na.rm = TRUE)) return(list())
  idx <- which(sig); cls <- list(); run <- nodes[idx[1]]
  if (length(idx) > 1) for (k in 2:length(idx)) {
    if (nodes[idx[k]] == nodes[idx[k - 1]] + 1) run <- c(run, nodes[idx[k]])
    else { cls[[length(cls) + 1]] <- run; run <- nodes[idx[k]] }
  }
  cls[[length(cls) + 1]] <- run; cls
}
maxcl <- function(sig, nodes) { cl <- clusters_from_sig(sig, nodes); if (!length(cl)) 0L else max(sapply(cl, length)) }

sig_mask <- !is.na(node_p) & node_p < alpha_node
obs_cl <- clusters_from_sig(sig_mask, node_idx)
obs_max <- if (length(obs_cl)) max(sapply(obs_cl, length)) else 0L
num_sig <- sum(sig_mask); num_cl <- length(obs_cl)

fit_red <- lm(red_formula, data = data.frame(y = y, covdf))
yhat <- fitted(fit_red); res <- resid(fit_red)
analysable <- which(sapply(node_cols, function(nc) sd(dat[[nc]]) > 0))
nodemat <- as.matrix(dat[, node_cols, drop = FALSE])

perm_fun <- function(p) {
  set.seed(rng_seed + p)
  yp <- yhat + res[sample.int(n_subj)]; pp <- rep(1, num_nodes)
  for (i in analysable) {
    fit <- lm(full_formula, data = data.frame(y = yp, node = nodemat[, i], covdf))
    sm <- summary(fit)$coefficients
    if ("node" %in% rownames(sm)) pp[i] <- 2 * pt(-abs(sm["node", "t value"]), df = fit$df.residual)
  }
  maxcl(pp < alpha_node, node_idx)
}
cores <- suppressWarnings(as.integer(Sys.getenv("R_PERM_CORES", unset = NA)))
if (is.na(cores) || cores < 1) cores <- max(1L, parallel::detectCores() - 1L)
perm_max <- unlist(parallel::mclapply(1:num_perm, perm_fun, mc.cores = cores))
ext_thr <- as.integer(quantile(perm_max, probs = 1 - alpha_fw, type = 1))
clp <- function(sz) mean(perm_max >= sz)

write.csv(data.frame(Node = node_idx, Estimate = node_est, t_value = node_t, p_value = node_p),
          file.path(out_dir, paste0(base, "_nodewise.csv")), row.names = FALSE)
if (num_cl > 0) {
  cl_df <- do.call(rbind, lapply(seq_along(obs_cl), function(k) {
    nodes <- obs_cl[[k]]; it <- match(nodes, node_idx); tv <- node_t[it]
    data.frame(ClusterID = k, Size = length(nodes), StartNode = min(nodes), EndNode = max(nodes),
               MeanTValue = mean(tv, na.rm = TRUE),
               Direction = ifelse(mean(tv, na.rm = TRUE) > 0, "Positive", "Negative"),
               ClusterPValue = clp(length(nodes)), ExtentThresholdNodes = ext_thr,
               PassExtentThreshold = length(nodes) >= ext_thr)
  }))
} else cl_df <- data.frame(ClusterID = integer(), Size = integer(), StartNode = integer(),
                           EndNode = integer(), MeanTValue = double(), Direction = character(),
                           ClusterPValue = double(), ExtentThresholdNodes = integer(),
                           PassExtentThreshold = logical())
write.csv(cl_df, file.path(out_dir, paste0(base, "_clusters.csv")), row.names = FALSE)
write.csv(data.frame(Outcome = response_col, MetricPrefix = metric_prefix, N_subjects = n_subj,
                     N_dropped = n_drop, NodesTested = num_nodes, NumPermutations = num_perm,
                     NumNodewiseSignificant = num_sig, NumClustersFormed = num_cl,
                     ObservedMaxClusterSize = obs_max, ExtentThresholdNodes = ext_thr,
                     NumClustersPassingExtent = if (num_cl > 0) sum(cl_df$PassExtentThreshold) else 0),
          file.path(out_dir, paste0(base, "_summary.csv")), row.names = FALSE)
cat("Done:", base, "clusters=", num_cl, "sig=", num_sig, "ext=", ext_thr, "\n")
