import Foundation
import SwiftSoup

// ============================================================================
// MARK: - Scraping Configuration
// If TechPowerUp changes their DOM, ONLY update the constants below.
// ============================================================================

enum ScrapingConfig {
    static let baseURL = "https://www.techpowerup.com"

    // Stage 1: Index page — motherboard review listing
    static let indexPath = "/review/?category=Motherboards&manufacturer="
    // Additional filter params appended after brand name
    static let indexSuffix = "&sort=date"

    // CSS selectors for the index table
    static let indexRowSelector  = "table.reviewlist tbody tr"
    static let indexLinkSelector = "a"  // first <a> in the row = detail link + title
    static let indexDateSelector = "td:last-child"

    // Stage 2: Detail page — extract manufacturer link
    static let detailLinkSelectors: [String] = [
        "a[href*='asus.com']",
        "a[href*='gigabyte.com']",
        "a[href*='msi.com']",
        "a[href*='asrock.com']",
        "a:containsOwn(Official Page)",
        "a:containsOwn(Manufacturer)",
        "a:containsOwn(Product Page)",
    ]

    // Known brand strings used for Stage 1 fetching
    static let brands = ["ASUS", "GIGABYTE", "MSI", "ASRock"]

    // Chipset keywords for auto-detection from model name
    static let knownChipsets = [
        // Intel
        "Z890", "B860", "Z790", "B760", "H770", "Z690", "B660", "H670", "Z590", "B560", "Z490", "B460",
        // AMD
        "X870E", "X870", "X670E", "X670", "B650E", "B650", "A620",
        "X570", "B550", "A520", "X470", "B450",
    ]
}

// ============================================================================
// MARK: - Scraping Engine
// ============================================================================

/// Responsible for all network fetching and HTML parsing.
/// The rest of the app never touches HTML — only this engine does.
final class ScrapingEngine {
    static let shared = ScrapingEngine()
    private let session: URLSession
    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        config.httpAdditionalHeaders = [
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ]
        session = URLSession(configuration: config)
    }

    // MARK: - Stage 1: Index Scrape

    /// Fetches the motherboard index for ALL brands.
    /// Returns a merged, deduplicated list sorted by brand then chipset.
    func fetchFullIndex() async throws -> [Motherboard] {
        try await withThrowingTaskGroup(of: [Motherboard].self) { group in
            for brand in ScrapingConfig.brands {
                group.addTask { [self] in
                    try await fetchIndex(brand: brand)
                }
            }
            var all: [Motherboard] = []
            for try await batch in group {
                all.append(contentsOf: batch)
            }
            // Deduplicate by id
            var seen = Set<String>()
            return all.filter { seen.insert($0.id).inserted }
                .sorted { ($0.brand, $0.chipset, $0.fullModelName) < ($1.brand, $1.chipset, $1.fullModelName) }
        }
    }

    /// Fetches the index for a single brand.
    func fetchIndex(brand: String) async throws -> [Motherboard] {
        let urlString = ScrapingConfig.baseURL
            + ScrapingConfig.indexPath
            + brand.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)!
            + ScrapingConfig.indexSuffix

        let html = try await fetchHTML(from: urlString)
        return try parseIndexPage(html, brand: brand)
    }

    // MARK: - Stage 2: Detail Scrape (On-Demand)

    /// Fetches the TPU detail page for a specific motherboard and extracts
    /// the official manufacturer URL.
    func fetchOfficialURL(for board: Motherboard) async throws -> String? {
        guard let detailPath = board.tpuDetailUrl else { return nil }

        let urlString: String
        if detailPath.hasPrefix("http") {
            urlString = detailPath
        } else {
            urlString = ScrapingConfig.baseURL + detailPath
        }

        let html = try await fetchHTML(from: urlString)
        return try parseDetailPage(html)
    }

    // MARK: - HTML Fetching

    private func fetchHTML(from urlString: String) async throws -> String {
        guard let url = URL(string: urlString) else {
            throw ScrapingError.invalidURL(urlString)
        }
        let (data, response) = try await session.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw ScrapingError.httpError((response as? HTTPURLResponse)?.statusCode ?? -1)
        }
        guard let html = String(data: data, encoding: .utf8) else {
            throw ScrapingError.decodingFailed
        }
        return html
    }

    // MARK: - Index Page Parser

    private func parseIndexPage(_ html: String, brand: String) throws -> [Motherboard] {
        let doc = try SwiftSoup.parse(html)
        let rows = try doc.select(ScrapingConfig.indexRowSelector)

        var boards: [Motherboard] = []

        for row in rows {
            guard let link = try row.select(ScrapingConfig.indexLinkSelector).first() else { continue }
            let title = try link.text().trimmingCharacters(in: .whitespacesAndNewlines)
            let href  = try link.attr("href")

            guard !title.isEmpty else { continue }

            // Derive chipset from the title
            let chipset = detectChipset(from: title) ?? "Unknown"

            // Build a clean model name (remove "Review" suffix if present)
            let modelName = title
                .replacingOccurrences(of: " Review", with: "")
                .replacingOccurrences(of: " review", with: "")
                .trimmingCharacters(in: .whitespacesAndNewlines)

            // Remove brand prefix from model name if present
            let cleanName = removeBrandPrefix(modelName, brand: brand)

            // Construct a stable ID from the href slug
            let slug = href
                .replacingOccurrences(of: "/review/", with: "")
                .replacingOccurrences(of: "/", with: "")
                .lowercased()
            let id = slug.isEmpty ? "\(brand)-\(cleanName)".slugified : slug

            let board = Motherboard(
                id: id,
                brand: brand,
                chipset: chipset,
                fullModelName: cleanName,
                tpuDetailUrl: href.isEmpty ? nil : href,
                officialSupportUrl: nil
            )
            boards.append(board)
        }

        return boards
    }

    // MARK: - Detail Page Parser

    private func parseDetailPage(_ html: String) throws -> String? {
        let doc = try SwiftSoup.parse(html)

        // Try each known selector pattern until we find a manufacturer link
        for selector in ScrapingConfig.detailLinkSelectors {
            if let link = try doc.select(selector).first() {
                let href = try link.attr("href")
                if href.hasPrefix("http") {
                    return href
                }
            }
        }

        // Broader fallback: look for any external link in the specs/info section
        let allLinks = try doc.select("a[href^='https://']")
        for link in allLinks {
            let href = try link.attr("href")
            for brand in ScrapingConfig.brands {
                if href.lowercased().contains(brand.lowercased()) &&
                   !href.contains("techpowerup") {
                    return href
                }
            }
        }

        return nil
    }

    // MARK: - Helpers

    private func detectChipset(from title: String) -> String? {
        let upper = title.uppercased()
        for chipset in ScrapingConfig.knownChipsets {
            if upper.contains(chipset.uppercased()) {
                return chipset
            }
        }
        return nil
    }

    private func removeBrandPrefix(_ name: String, brand: String) -> String {
        let prefixes = [brand, brand.uppercased(), brand.lowercased()]
        var result = name
        for prefix in prefixes {
            if result.hasPrefix(prefix + " ") {
                result = String(result.dropFirst(prefix.count + 1))
                break
            }
        }
        return result
    }
}

// MARK: - Error Types

enum ScrapingError: LocalizedError {
    case invalidURL(String)
    case httpError(Int)
    case decodingFailed
    case parsingFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL(let url):     return "Invalid URL: \(url)"
        case .httpError(let code):     return "HTTP error: \(code)"
        case .decodingFailed:          return "Failed to decode HTML as UTF-8"
        case .parsingFailed(let msg):  return "Parse error: \(msg)"
        }
    }
}

// MARK: - String Extension

extension String {
    var slugified: String {
        lowercased()
            .replacingOccurrences(of: " ", with: "-")
            .replacingOccurrences(of: "/", with: "-")
            .filter { $0.isLetter || $0.isNumber || $0 == "-" }
    }
}
