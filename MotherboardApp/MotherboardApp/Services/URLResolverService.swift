import Foundation

/// Decoupled URL resolution service.
/// The UI NEVER constructs URLs — it always goes through this service.
///
/// Resolution order:
/// 1. Return cached `officialSupportUrl` if available
/// 2. Attempt Stage 2 scrape from TPU detail page
/// 3. Fallback: construct a Google Search URL using `fullModelName`
struct URLResolverService {

    /// Resolves the best available URL for a motherboard.
    /// Guaranteed to always return a valid URL (Google fallback).
    static func resolve(for board: Motherboard) async -> URL {
        // 1. Check if we already have a cached official URL
        if let cached = board.officialSupportUrl,
           let url = URL(string: cached) {
            return attemptSupportURL(from: url, brand: board.brand)
        }

        // 2. Try Stage 2 scrape
        do {
            if let officialString = try await ScrapingEngine.shared.fetchOfficialURL(for: board),
               let url = URL(string: officialString) {
                // Persist to cache for future use
                CacheService.shared.updateOfficialURL(officialString, for: board.id)
                return attemptSupportURL(from: url, brand: board.brand)
            }
        } catch {
            // Scrape failed — fall through to Google fallback
            print("[URLResolver] Stage 2 failed for \(board.id): \(error.localizedDescription)")
        }

        // 3. Google Search fallback (self-healing)
        return constructGoogleFallback(for: board)
    }

    // MARK: - Support URL Heuristic

    /// Attempts to transform a marketing/product URL into a support/download URL.
    /// Each brand has different URL conventions.
    private static func attemptSupportURL(from url: URL, brand: String) -> URL {
        let urlString = url.absoluteString

        switch brand.uppercased() {
        case "ASUS":
            // ASUS support pages typically end with /helpdesk_download/
            if !urlString.contains("helpdesk") && !urlString.contains("HelpDesk") {
                let supportURL = urlString.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
                    + "/helpdesk_download/"
                if let u = URL(string: supportURL) { return u }
            }

        case "GIGABYTE":
            // GIGABYTE support pages use /support/ path
            if urlString.contains("/Motherboard/") && !urlString.lowercased().contains("support") {
                let supportURL = urlString
                    .replacingOccurrences(of: "#", with: "/support#")
                if let u = URL(string: supportURL) { return u }
            }

        case "MSI":
            // MSI support URL pattern: /Motherboard/support/MODEL
            if urlString.contains("/Motherboard/") && !urlString.contains("/support/") {
                let supportURL = urlString
                    .replacingOccurrences(of: "/Motherboard/", with: "/Motherboard/support/")
                if let u = URL(string: supportURL) { return u }
            }

        case "ASROCK":
            // ASRock — download page at /Specification.asp path
            if urlString.contains("/mb/") && !urlString.contains("Specification") {
                let supportURL = urlString.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
                    + "/Specification.asp"
                if let u = URL(string: supportURL) { return u }
            }

        default:
            break
        }

        // If no transform matched, return original URL
        return url
    }

    // MARK: - Google Fallback

    /// Constructs a Google search URL as the ultimate fallback.
    /// This ensures the user ALWAYS gets a useful result, even if scraping is broken.
    static func constructGoogleFallback(for board: Motherboard) -> URL {
        let query = "\(board.brand) \(board.fullModelName) Official Support site"
            .addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        return URL(string: "https://www.google.com/search?q=\(query)")!
    }
}
