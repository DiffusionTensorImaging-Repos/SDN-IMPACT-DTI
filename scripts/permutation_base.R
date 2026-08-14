# =========================================================================
# Base-R port of permutation_one.R (no readr/dplyr/foreach/tibble).
# Identical model + Freedman-Lane cluster-extent test. Serial permutation loop,
# which is exactly the branch permutation_one.R takes when R_PERM_CORES=1.
# Args: data_csv response_col metric_prefix out_dir base_label
# =========================================================================
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) >= 5)
data_csv <- args[1]; response_col <- args[2]; metric_prefix <- args[3]
out_dir  <- args[4]; base <- args[5]

covariate_cols  <- c("ICV", "Mean_tckstats", "Count_tckstats", "absolute_motion", "maternal_age")
alpha_node      <- 0.05
alpha_familywise<- 0.05
num_permutations<- as.integer(Sys.getenv("R_PERM_N", unset = "5000"))
rng_seed        <- 123
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

dat <- read.csv(data_csv, check.names = FALSE, stringsAsFactors = FALSE)

node_cols <- grep(paste0("^", metric_prefix, "[0-9]+$"), names(dat), value = TRUE)
if (length(node_cols) == 0) stop("No columns matching ", metric_prefix, "0.. in: ", data_csv)
node_idx  <- as.integer(sub(paste0("^", metric_prefix), "", node_cols))
ord <- order(node_idx); node_cols <- node_cols[ord]; node_idx <- node_idx[ord]
num_nodes <- length(node_cols)

dat[[response_col]] <- as.numeric(dat[[response_col]])
for (cc in covariate_cols) dat[[cc]] <- as.numeric(dat[[cc]])

all_model_cols <- c(response_col, covariate_cols, node_cols)
mask <- complete.cases(dat[, all_model_cols])
n_dropped <- sum(!mask)
dat <- dat[mask, , drop = FALSE]
n_subj <- nrow(dat)
if (n_subj < 5) { message("Fewer than 5 subjects — skipping ", base); quit(status = 0) }

y <- dat[[response_col]]
covdf <- dat[, covariate_cols, drop = FALSE]
full_formula <- as.formula(paste("y ~ node +", paste(covariate_cols, collapse = " + ")))
red_formula  <- as.formula(paste("y ~", paste(covariate_cols, collapse = " + ")))

fit_node_full <- function(nodevals) {
  df0 <- data.frame(y = y, node = nodevals, covdf)
  df0 <- df0[complete.cases(df0), ]
  if (nrow(df0) < 3 || sd(df0$node) == 0) return(c(Estimate = NA, t = NA, p = NA, df = NA, n = nrow(df0)))
  fit <- lm(full_formula, data = df0)
  sm  <- summary(fit)$coefficients
  if (!("node" %in% rownames(sm))) return(c(Estimate = NA, t = NA, p = NA, df = fit$df.residual, n = nrow(df0)))
  tval <- unname(sm["node", "t value"]); est <- unname(sm["node", "Estimate"])
  pval <- 2 * pt(-abs(tval), df = fit$df.residual)
  c(Estimate = est, t = tval, p = pval, df = fit$df.residual, n = nrow(df0))
}

set.seed(rng_seed)
node_stats <- t(vapply(node_cols, function(nc) fit_node_full(dat[[nc]]), numeric(5)))
node_stats_df <- data.frame(Node = node_idx, Estimate = node_stats[, "Estimate"],
  t_value = node_stats[, "t"], p_value = node_stats[, "p"],
  df = node_stats[, "df"], n = node_stats[, "n"])
write.csv(node_stats_df, file.path(out_dir, paste0(base, "_nodewise.csv")), row.names = FALSE)

clusters_from_sig <- function(sig, nodes_numeric) {
  if (!any(sig, na.rm = TRUE)) return(list())
  idx <- which(sig); cls <- list(); run <- c(nodes_numeric[idx[1]])
  if (length(idx) > 1) for (k in 2:length(idx)) {
    if (nodes_numeric[idx[k]] == nodes_numeric[idx[k - 1]] + 1) run <- c(run, nodes_numeric[idx[k]])
    else { cls[[length(cls) + 1]] <- run; run <- c(nodes_numeric[idx[k]]) }
  }
  cls[[length(cls) + 1]] <- run; cls
}
max_cluster_size_from_sig <- function(sig, nodes_numeric) {
  cls <- clusters_from_sig(sig, nodes_numeric)
  if (length(cls) == 0) 0L else max(vapply(cls, length, 1L))
}

sig_mask <- !is.na(node_stats_df$p_value) & node_stats_df$p_value < alpha_node
obs_clusters <- clusters_from_sig(sig_mask, node_stats_df$Node)
obs_sizes <- vapply(obs_clusters, length, 1L)
obs_max_size <- if (length(obs_sizes)) max(obs_sizes) else 0L
num_sig_nodes <- sum(sig_mask); num_clusters <- length(obs_clusters)

fit_red <- lm(red_formula, data = data.frame(y = y, covdf))
yhat_red <- fitted(fit_red); resid_red <- resid(fit_red)
analysable <- vapply(node_cols, function(nc) sd(dat[[nc]]) > 0, logical(1))

perm_fun <- function(.p) {
  y_perm <- yhat_red + resid_red[sample.int(n_subj)]
  p_perm <- rep(1, num_nodes)
  for (i in which(analysable)) {
    fit <- lm(full_formula, data = data.frame(y = y_perm, node = dat[[node_cols[i]]], covdf))
    sm <- summary(fit)$coefficients
    if ("node" %in% rownames(sm)) p_perm[i] <- 2 * pt(-abs(sm["node", "t value"]), df = fit$df.residual)
  }
  max_cluster_size_from_sig(p_perm < alpha_node, node_idx)
}
perm_max_sizes <- vapply(1:num_permutations, perm_fun, integer(1))

extent_threshold <- as.integer(quantile(perm_max_sizes, probs = 1 - alpha_familywise, type = 1))
cluster_p_from_size <- function(size) mean(perm_max_sizes >= size)

if (num_clusters > 0) {
  rows <- lapply(seq_along(obs_clusters), function(k) {
    nodes <- obs_clusters[[k]]; it <- match(nodes, node_stats_df$Node)
    tv <- node_stats_df$t_value[it]; es <- node_stats_df$Estimate[it]
    data.frame(ClusterID = k, Size = length(nodes), StartNode = min(nodes), EndNode = max(nodes),
      Nodes = paste(nodes, collapse = ","), MeanTValue = mean(tv, na.rm = TRUE),
      Direction = ifelse(mean(tv, na.rm = TRUE) > 0, "Positive", "Negative"),
      MaxAbsTValue = tv[which.max(abs(tv))], MaxAbsTNode = nodes[which.max(abs(tv))],
      MeanEstimate = mean(es, na.rm = TRUE), ClusterPValue = cluster_p_from_size(length(nodes)),
      ExtentThresholdNodes = extent_threshold, PassExtentThreshold = length(nodes) >= extent_threshold)
  })
  all_clusters_df <- do.call(rbind, rows)
} else {
  all_clusters_df <- data.frame(ClusterID = integer(), Size = integer(), StartNode = integer(),
    EndNode = integer(), Nodes = character(), MeanTValue = double(), Direction = character(),
    MaxAbsTValue = double(), MaxAbsTNode = integer(), MeanEstimate = double(),
    ClusterPValue = double(), ExtentThresholdNodes = integer(), PassExtentThreshold = logical())
}
write.csv(all_clusters_df, file.path(out_dir, paste0(base, "_clusters.csv")), row.names = FALSE)

summary_df <- data.frame(Outcome = response_col, MetricPrefix = metric_prefix,
  Covariates = paste(covariate_cols, collapse = ", "), N_subjects = n_subj, N_dropped = n_dropped,
  NodesTested = num_nodes, NodewiseAlpha = alpha_node, FamilywiseAlpha = alpha_familywise,
  NumPermutations = num_permutations, NumNodewiseSignificant = num_sig_nodes,
  NumClustersFormed = num_clusters, ObservedMaxClusterSize = obs_max_size,
  ExtentThresholdNodes = extent_threshold,
  NumClustersPassingExtent = sum(all_clusters_df$PassExtentThreshold, na.rm = TRUE))
write.csv(summary_df, file.path(out_dir, paste0(base, "_summary.csv")), row.names = FALSE)
cat("Done:", base, "clusters=", num_clusters, "sig=", num_sig_nodes, "ext=", extent_threshold, "\n")
