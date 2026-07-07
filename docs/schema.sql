-- =============================================================================
-- Schema MySQL CMS femturisme.cat (estructura sense dades)
-- =============================================================================
-- Origen:     export phpMyAdmin del client (2026-07-07)
-- Base:       femturisme
-- Motor:      MariaDB 10.3.39 (Debian)
-- Taules:     86
-- Ús:         Fase 2 sql-mapeo, Fase 3 repositories (read-only)
-- NOTA:       No commitar dumps amb dades / PII — veure docs/devs/desenvolupament-local.md §9
-- =============================================================================
-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Servidor: localhost
-- Temps de generaciÃ³: 07-07-2026 a les 11:55:48
-- VersiÃ³ del servidor: 10.3.39-MariaDB-0+deb10u1
-- VersiÃ³ de PHP: 7.4.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de dades: `femturisme`
--

-- --------------------------------------------------------

--
-- Estructura de la taula `agenda_categories`
--

CREATE TABLE `agenda_categories` (
  `id` int(11) NOT NULL,
  `id_agenda` int(11) NOT NULL,
  `id_categoria` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `agenda_clients`
--

CREATE TABLE `agenda_clients` (
  `id` int(11) NOT NULL,
  `id_agenda` int(11) NOT NULL,
  `codi_client` varchar(11) NOT NULL DEFAULT '',
  `id_element` int(11) NOT NULL,
  `tipus` varchar(15) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `agenda_continguts`
--

CREATE TABLE `agenda_continguts` (
  `id` int(11) NOT NULL,
  `id_agenda` int(11) NOT NULL DEFAULT 0,
  `param_url` mediumtext NOT NULL DEFAULT '',
  `titol` varchar(500) NOT NULL DEFAULT '',
  `descripcio` mediumtext DEFAULT NULL,
  `idioma` varchar(50) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- --------------------------------------------------------

--
-- Estructura de la taula `agenda_dates`
--

CREATE TABLE `agenda_dates` (
  `id` int(11) NOT NULL,
  `id_agenda` int(11) NOT NULL,
  `data_inici` date NOT NULL,
  `data_final` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `agenda_etiquetes`
--

CREATE TABLE `agenda_etiquetes` (
  `id` int(11) NOT NULL,
  `id_agenda` int(11) NOT NULL DEFAULT 0,
  `id_etiqueta` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `agenda_general`
--

CREATE TABLE `agenda_general` (
  `id` int(255) NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `adreca` text DEFAULT NULL,
  `latitud` varchar(255) NOT NULL DEFAULT '',
  `longitud` varchar(255) NOT NULL DEFAULT '',
  `activa` tinyint(1) NOT NULL DEFAULT 0,
  `periodica` tinyint(1) NOT NULL DEFAULT 0,
  `arxivada` tinyint(1) NOT NULL DEFAULT 0,
  `baixa` tinyint(1) NOT NULL DEFAULT 0,
  `recomanada` tinyint(1) NOT NULL DEFAULT 0,
  `nens` tinyint(1) NOT NULL DEFAULT 0,
  `gratuita` tinyint(1) NOT NULL DEFAULT 0,
  `multiples_dates` text DEFAULT NULL,
  `diada` tinyint(1) NOT NULL DEFAULT 0,
  `newsletter` tinyint(1) NOT NULL DEFAULT 0,
  `imatge` varchar(255) NOT NULL DEFAULT '',
  `preu` varchar(50) NOT NULL DEFAULT '',
  `link` varchar(255) NOT NULL DEFAULT '',
  `entrades` varchar(255) DEFAULT '',
  `adjunt` varchar(250) NOT NULL DEFAULT '',
  `intro_xarxes` varchar(255) NOT NULL DEFAULT '',
  `observacions` text DEFAULT NULL,
  `promocions` text DEFAULT NULL,
  `logs` text DEFAULT NULL,
  `mesos` varchar(250) NOT NULL DEFAULT '',
  `falta_programa` tinyint(1) NOT NULL DEFAULT 0,
  `puntual` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `agenda_oberta`
--

CREATE TABLE `agenda_oberta` (
  `id` int(11) NOT NULL,
  `data_inici` datetime NOT NULL,
  `data_fi` datetime NOT NULL,
  `data_actualitzacio` datetime DEFAULT NULL,
  `resum` text NOT NULL,
  `descripcio` text NOT NULL,
  `imatge` varchar(255) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  `adreca` varchar(255) DEFAULT NULL,
  `latitud` varchar(50) NOT NULL,
  `longitud` varchar(50) NOT NULL,
  `categories` varchar(250) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `agenda_pobles`
--

CREATE TABLE `agenda_pobles` (
  `id` int(11) NOT NULL,
  `id_agenda` int(11) NOT NULL,
  `id_poble` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `agendes_externes`
--

CREATE TABLE `agendes_externes` (
  `id` bigint(20) NOT NULL,
  `id_extern` varchar(255) NOT NULL,
  `origen_agenda` varchar(255) DEFAULT NULL,
  `titol` varchar(255) DEFAULT NULL,
  `descripcio` mediumtext DEFAULT NULL,
  `data_inici` date DEFAULT NULL,
  `data_fi` date DEFAULT NULL,
  `municipi` varchar(255) DEFAULT NULL,
  `adreca` varchar(255) DEFAULT NULL,
  `coordenades` varchar(255) DEFAULT NULL,
  `categories` varchar(255) DEFAULT NULL,
  `imatges` mediumtext DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `estat` varchar(50) NOT NULL DEFAULT 'pendent',
  `preu` text DEFAULT NULL,
  `subtitol` varchar(255) DEFAULT NULL,
  `enllacos` mediumtext DEFAULT NULL,
  `horari` text DEFAULT NULL,
  `tags_categories` varchar(255) DEFAULT NULL,
  `tags_ambits` varchar(255) DEFAULT NULL,
  `comarca_i_municipi` varchar(255) DEFAULT NULL,
  `espai` varchar(255) DEFAULT NULL,
  `url` varchar(105) DEFAULT NULL,
  `API_NOM` varchar(50) DEFAULT NULL,
  `id_agenda` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `analytics_data`
--

CREATE TABLE `analytics_data` (
  `tipus_element` varchar(50) NOT NULL,
  `id` int(11) NOT NULL,
  `mes` int(11) NOT NULL,
  `any` int(11) NOT NULL,
  `total` int(11) NOT NULL,
  `tipus` varchar(50) NOT NULL,
  `accio` varchar(50) NOT NULL,
  `categoria` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `banners_ubicacio`
--

CREATE TABLE `banners_ubicacio` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_banner` int(11) NOT NULL DEFAULT 0,
  `tipus` varchar(20) DEFAULT NULL,
  `id_element` int(11) NOT NULL DEFAULT 0,
  `posicio` int(1) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `banner_clients`
--

CREATE TABLE `banner_clients` (
  `id` int(11) NOT NULL,
  `id_banner` int(11) NOT NULL,
  `codi_client` varchar(11) DEFAULT NULL,
  `id_element` int(11) NOT NULL,
  `tipus` varchar(15) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `banner_contingut`
--

CREATE TABLE `banner_contingut` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_banner` int(10) NOT NULL,
  `idioma` varchar(2) NOT NULL,
  `titol` varchar(150) NOT NULL,
  `resum` mediumtext NOT NULL,
  `url` varchar(255) NOT NULL,
  `target` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- --------------------------------------------------------

--
-- Estructura de la taula `banner_general`
--

CREATE TABLE `banner_general` (
  `id` int(11) NOT NULL,
  `data_inicial` date NOT NULL,
  `data_final` date NOT NULL,
  `data_fixat` date DEFAULT NULL,
  `data_fixat_final` date DEFAULT NULL,
  `track_link` varchar(150) DEFAULT NULL,
  `tipus` varchar(20) NOT NULL,
  `fixat` int(11) DEFAULT NULL,
  `primer` int(11) NOT NULL,
  `imatge` varchar(255) NOT NULL DEFAULT '',
  `imatge2` varchar(255) NOT NULL DEFAULT '',
  `actiu` int(1) NOT NULL,
  `newsletter` int(1) NOT NULL,
  `periodic` int(1) NOT NULL,
  `campanya` tinyint(1) NOT NULL DEFAULT 0,
  `observacions` text NOT NULL,
  `promocions` text DEFAULT NULL,
  `codi_client` varchar(15) DEFAULT NULL,
  `id_poble` int(11) NOT NULL,
  `logs` text NOT NULL,
  `pes` decimal(4,2) NOT NULL DEFAULT 1.00,
  `data_pes_inicial` date DEFAULT NULL,
  `data_pes_final` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ci_captcha`
--

CREATE TABLE `ci_captcha` (
  `captcha_id` bigint(13) UNSIGNED NOT NULL,
  `captcha_time` int(10) UNSIGNED NOT NULL,
  `ip_address` varchar(16) NOT NULL DEFAULT '0',
  `word` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ci_sessions`
--

CREATE TABLE `ci_sessions` (
  `session_id` varchar(40) NOT NULL DEFAULT '0',
  `ip_address` varchar(45) NOT NULL DEFAULT '0',
  `user_agent` varchar(120) NOT NULL,
  `last_activity` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `user_data` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `client`
--

CREATE TABLE `client` (
  `id` int(11) NOT NULL,
  `codi_client` varchar(15) NOT NULL DEFAULT '',
  `id_element` int(11) DEFAULT NULL,
  `tipus` varchar(15) NOT NULL DEFAULT '',
  `nom` varchar(250) NOT NULL DEFAULT '',
  `baixa` tinyint(4) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `comunicacions`
--

CREATE TABLE `comunicacions` (
  `id` int(11) NOT NULL,
  `data` date NOT NULL,
  `tipus` varchar(50) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
  `id_establiment` int(11) DEFAULT 0,
  `id_poble` int(11) DEFAULT 0,
  `status` varchar(25) NOT NULL,
  `assumpte` text DEFAULT NULL,
  `contingut` text DEFAULT NULL,
  `destinataris_textarea` text DEFAULT NULL,
  `log` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- --------------------------------------------------------

--
-- Estructura de la taula `config`
--

CREATE TABLE `config` (
  `id` int(11) NOT NULL,
  `name` varchar(250) NOT NULL,
  `value` varchar(250) NOT NULL,
  `updated` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `counters`
--

CREATE TABLE `counters` (
  `id` int(11) NOT NULL,
  `tipus` varchar(255) NOT NULL,
  `counter` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `destacats`
--

CREATE TABLE `destacats` (
  `id` int(11) NOT NULL,
  `id_establiment` int(11) NOT NULL,
  `data_inicial` date NOT NULL,
  `data_final` date NOT NULL,
  `tipus` varchar(15) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `establiment_certificats`
--

CREATE TABLE `establiment_certificats` (
  `id` int(11) UNSIGNED NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `id_certificat` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `establiment_continguts`
--

CREATE TABLE `establiment_continguts` (
  `id` int(11) UNSIGNED NOT NULL,
  `id_establiment` int(11) DEFAULT NULL,
  `idioma` varchar(2) NOT NULL DEFAULT '',
  `introduccio` mediumtext DEFAULT NULL,
  `contingut` mediumtext DEFAULT NULL,
  `description` mediumtext DEFAULT NULL,
  `keywords` mediumtext DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- --------------------------------------------------------

--
-- Estructura de la taula `establiment_etiquetes`
--

CREATE TABLE `establiment_etiquetes` (
  `id` int(11) NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `id_etiqueta` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `establiment_general`
--

CREATE TABLE `establiment_general` (
  `id` int(11) NOT NULL,
  `param_url` varchar(150) DEFAULT NULL,
  `id_booking` varchar(64) NOT NULL DEFAULT '',
  `reserves_url` varchar(400) NOT NULL DEFAULT '',
  `tipus` int(11) DEFAULT NULL,
  `nom` varchar(150) DEFAULT NULL,
  `correu_reserves` varchar(150) NOT NULL DEFAULT '',
  `correu` varchar(150) DEFAULT NULL,
  `adreca` text DEFAULT NULL,
  `codi_postal` varchar(10) NOT NULL DEFAULT '',
  `id_poble` int(11) DEFAULT NULL,
  `estrelles` int(11) DEFAULT NULL,
  `qualitat` int(11) DEFAULT NULL,
  `nostre` int(11) DEFAULT NULL,
  `telf` varchar(50) NOT NULL DEFAULT '',
  `whatsapp` varchar(100) NOT NULL DEFAULT '',
  `web` varchar(400) NOT NULL DEFAULT '',
  `link` varchar(400) DEFAULT NULL,
  `observacions` text DEFAULT NULL,
  `promocions` text DEFAULT NULL,
  `fax` varchar(15) DEFAULT NULL,
  `codi_rtc` varchar(250) NOT NULL DEFAULT '',
  `data_creacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_baixa` date DEFAULT NULL,
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `actiu` tinyint(1) NOT NULL DEFAULT 0,
  `latitud` varchar(45) NOT NULL DEFAULT '',
  `longitud` varchar(45) NOT NULL DEFAULT '',
  `web_ft` tinyint(1) DEFAULT 0,
  `allow_propostes` tinyint(1) NOT NULL DEFAULT 0,
  `video` varchar(250) NOT NULL DEFAULT '',
  `imatge` varchar(250) NOT NULL DEFAULT '',
  `imatge_header` varchar(250) NOT NULL DEFAULT '',
  `id_fitxa` int(11) NOT NULL DEFAULT 0,
  `codi_client` varchar(15) NOT NULL DEFAULT '',
  `contracte` varchar(64) NOT NULL DEFAULT '',
  `password` varchar(250) NOT NULL DEFAULT '',
  `xs_facebook` varchar(100) NOT NULL DEFAULT '',
  `xs_twitter` varchar(100) NOT NULL DEFAULT '',
  `xs_instagram` varchar(100) NOT NULL DEFAULT '',
  `xs_youtube` varchar(100) NOT NULL DEFAULT '',
  `xs_tiktok` varchar(100) NOT NULL DEFAULT '',
  `xs_tripadvisor` varchar(150) NOT NULL DEFAULT '',
  `xs_googlebusinessprofile` varchar(100) NOT NULL DEFAULT '',
  `ens` tinyint(1) NOT NULL DEFAULT 0,
  `sense_fitxa` tinyint(4) NOT NULL DEFAULT 0,
  `en_campanya` tinyint(1) NOT NULL DEFAULT 0,
  `last_analytics` varchar(15) NOT NULL DEFAULT '',
  `capacitat` varchar(150) NOT NULL DEFAULT '',
  `logs` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `establiment_pobles`
--

CREATE TABLE `establiment_pobles` (
  `id` int(11) UNSIGNED NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `id_poble` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `establiment_tipus`
--

CREATE TABLE `establiment_tipus` (
  `id` int(11) UNSIGNED NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `id_tipus` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `fitxa`
--

CREATE TABLE `fitxa` (
  `id` int(11) NOT NULL,
  `hash` varchar(150) NOT NULL,
  `comercial` int(11) NOT NULL,
  `nom` varchar(150) DEFAULT NULL,
  `tipus` varchar(150) NOT NULL,
  `adreca` varchar(150) NOT NULL DEFAULT '',
  `id_poble` int(11) DEFAULT NULL,
  `codi_postal` varchar(10) NOT NULL,
  `latitud` varchar(45) NOT NULL DEFAULT '',
  `longitud` varchar(45) NOT NULL DEFAULT '',
  `telefon` varchar(45) NOT NULL DEFAULT '',
  `email` varchar(150) NOT NULL DEFAULT '',
  `web` varchar(150) NOT NULL DEFAULT '',
  `codi_rtc` varchar(50) NOT NULL,
  `id_tipus` int(11) DEFAULT NULL,
  `contacte` varchar(150) NOT NULL,
  `id_booking` varchar(150) NOT NULL DEFAULT '',
  `reserves_url` varchar(400) NOT NULL,
  `facebook` varchar(150) NOT NULL DEFAULT '',
  `twitter` varchar(150) NOT NULL DEFAULT '',
  `googleplus` varchar(150) NOT NULL DEFAULT '',
  `instagram` varchar(150) NOT NULL DEFAULT '',
  `youtube` varchar(150) NOT NULL DEFAULT '',
  `fact_empresa` varchar(150) NOT NULL DEFAULT '',
  `fact_adreca` varchar(150) NOT NULL DEFAULT '',
  `fact_id_poble` varchar(150) NOT NULL DEFAULT '',
  `fact_codi_postal` varchar(10) NOT NULL,
  `fact_nif` varchar(150) NOT NULL DEFAULT '',
  `fact_iban` varchar(150) NOT NULL DEFAULT '',
  `fact_swift` varchar(150) NOT NULL DEFAULT '',
  `fact_email` varchar(150) NOT NULL DEFAULT '',
  `fact_telefon` varchar(150) NOT NULL DEFAULT '',
  `fact_contacte` varchar(150) NOT NULL DEFAULT '',
  `contingut` text NOT NULL,
  `observacions_client` text DEFAULT NULL,
  `observacions_comercial` text DEFAULT NULL,
  `logs` text DEFAULT NULL,
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `status` varchar(50) NOT NULL DEFAULT '0',
  `codi_client` varchar(15) NOT NULL,
  `video` varchar(255) NOT NULL DEFAULT '',
  `whatsapp` varchar(100) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `generic_categoria_agenda`
--

CREATE TABLE `generic_categoria_agenda` (
  `id` int(11) NOT NULL,
  `code` varchar(255) NOT NULL,
  `categoria_ca` varchar(255) NOT NULL,
  `categoria_es` varchar(255) NOT NULL,
  `categoria_fr` varchar(255) NOT NULL,
  `categoria_en` varchar(255) NOT NULL,
  `ordre` int(11) NOT NULL,
  `actiu` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `generic_categoria_oferta`
--

CREATE TABLE `generic_categoria_oferta` (
  `id` int(11) NOT NULL DEFAULT 0,
  `code` varchar(50) NOT NULL,
  `admin_desc` varchar(150) NOT NULL DEFAULT '',
  `categoria_ca` varchar(50) NOT NULL DEFAULT '',
  `categoria_es` varchar(50) NOT NULL DEFAULT '',
  `categoria_fr` varchar(50) NOT NULL,
  `categoria_en` varchar(50) NOT NULL,
  `ordre` int(11) NOT NULL DEFAULT 0,
  `actiu` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `generic_certificats`
--

CREATE TABLE `generic_certificats` (
  `id` int(11) NOT NULL,
  `code` varchar(150) NOT NULL DEFAULT '',
  `ordre` int(11) NOT NULL DEFAULT 0,
  `tipus` varchar(100) NOT NULL DEFAULT '',
  `certificat_ca` varchar(150) NOT NULL DEFAULT '',
  `certificat_es` varchar(150) NOT NULL DEFAULT '',
  `certificat_en` varchar(150) NOT NULL DEFAULT '',
  `certificat_fr` varchar(150) NOT NULL DEFAULT '',
  `url_ca` varchar(200) NOT NULL DEFAULT '',
  `url_es` varchar(200) NOT NULL DEFAULT '',
  `url_en` varchar(200) NOT NULL DEFAULT '',
  `url_fr` varchar(200) NOT NULL DEFAULT '',
  `actiu` tinyint(4) NOT NULL DEFAULT 1
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `generic_public`
--

CREATE TABLE `generic_public` (
  `id` int(11) NOT NULL,
  `public_ca` varchar(100) NOT NULL DEFAULT '',
  `public_es` varchar(100) NOT NULL DEFAULT '',
  `public_fr` varchar(100) NOT NULL,
  `public_en` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `generic_tematiques`
--

CREATE TABLE `generic_tematiques` (
  `id` int(11) NOT NULL,
  `code` varchar(50) NOT NULL,
  `tematica_ca` varchar(100) NOT NULL DEFAULT '',
  `tematica_es` varchar(100) NOT NULL DEFAULT '',
  `tematica_fr` varchar(100) NOT NULL,
  `tematica_en` varchar(100) NOT NULL,
  `h1_sufix_ca` varchar(80) DEFAULT '',
  `h1_sufix_es` varchar(80) DEFAULT '',
  `h1_sufix_en` varchar(80) DEFAULT '',
  `h1_sufix_fr` varchar(80) DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `generic_tipus_establiment`
--

CREATE TABLE `generic_tipus_establiment` (
  `id` int(11) NOT NULL DEFAULT 0,
  `code` varchar(50) NOT NULL,
  `tipus_ca` varchar(50) NOT NULL DEFAULT '',
  `tipus_es` varchar(50) NOT NULL DEFAULT '',
  `tipus_fr` varchar(50) NOT NULL,
  `tipus_en` varchar(50) NOT NULL,
  `ordre` int(11) NOT NULL DEFAULT 0,
  `actiu` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `generic_ubicacions`
--

CREATE TABLE `generic_ubicacions` (
  `id` int(11) NOT NULL,
  `ubicacio` varchar(255) NOT NULL,
  `param_url` varchar(255) NOT NULL,
  `id_provincia` int(11) NOT NULL DEFAULT 0,
  `id_comarca` int(11) NOT NULL DEFAULT 0,
  `id_element` int(11) NOT NULL,
  `id_pobles` text DEFAULT NULL,
  `param_pobles` text DEFAULT NULL,
  `latitud` varchar(50) NOT NULL,
  `longitud` varchar(50) NOT NULL,
  `distancia` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `idiomes`
--

CREATE TABLE `idiomes` (
  `id` int(11) NOT NULL DEFAULT 0,
  `principal` int(11) NOT NULL DEFAULT 0,
  `ordre` int(11) NOT NULL DEFAULT 0,
  `actiu` int(11) NOT NULL DEFAULT 0,
  `idioma` char(2) NOT NULL DEFAULT ''
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `landing_categories`
--

CREATE TABLE `landing_categories` (
  `id` int(11) NOT NULL,
  `id_landing` int(11) NOT NULL DEFAULT 0,
  `id_categoria` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `landing_categories_continguts`
--

CREATE TABLE `landing_categories_continguts` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_categoria` int(10) NOT NULL,
  `idioma` varchar(2) NOT NULL,
  `param_url` varchar(250) NOT NULL DEFAULT '',
  `titol` varchar(255) NOT NULL DEFAULT '',
  `contingut` text NOT NULL,
  `hashtag` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `landing_categories_general`
--

CREATE TABLE `landing_categories_general` (
  `id` int(10) UNSIGNED NOT NULL,
  `actiu` tinyint(1) UNSIGNED DEFAULT NULL,
  `campanya` tinyint(1) NOT NULL,
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `imatge` varchar(150) NOT NULL DEFAULT '',
  `imatge_header` varchar(150) NOT NULL DEFAULT '',
  `oculta_imatge` tinyint(1) NOT NULL,
  `ordre` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `logs` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `landing_continguts`
--

CREATE TABLE `landing_continguts` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_landing` int(10) NOT NULL,
  `idioma` varchar(2) NOT NULL,
  `param_url` varchar(250) NOT NULL DEFAULT '',
  `titol` varchar(255) NOT NULL DEFAULT '',
  `contingut` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `landing_etiquetes`
--

CREATE TABLE `landing_etiquetes` (
  `id` int(11) NOT NULL,
  `id_landing` int(11) NOT NULL DEFAULT 0,
  `id_etiqueta` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `landing_etiquetes_general`
--

CREATE TABLE `landing_etiquetes_general` (
  `id` int(10) UNSIGNED NOT NULL,
  `etiqueta` varchar(255) NOT NULL DEFAULT '',
  `actiu` tinyint(1) UNSIGNED DEFAULT NULL,
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `logs` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `landing_general`
--

CREATE TABLE `landing_general` (
  `id` int(10) UNSIGNED NOT NULL,
  `actiu` tinyint(1) UNSIGNED DEFAULT NULL,
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `imatge` varchar(150) NOT NULL DEFAULT '',
  `imatge_header` varchar(150) NOT NULL DEFAULT '',
  `oculta_imatge` tinyint(1) NOT NULL,
  `ordre` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `campanya` tinyint(4) NOT NULL,
  `data_revisio` date DEFAULT NULL,
  `logs` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `newsletter_continguts`
--

CREATE TABLE `newsletter_continguts` (
  `id` int(11) NOT NULL,
  `id_newsletter` int(11) NOT NULL,
  `tipus` varchar(25) NOT NULL,
  `id_element` int(11) NOT NULL,
  `ordre` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- --------------------------------------------------------

--
-- Estructura de la taula `newsletter_general`
--

CREATE TABLE `newsletter_general` (
  `id` int(11) NOT NULL,
  `titol_ca` text NOT NULL,
  `titol_es` text NOT NULL,
  `cos_ca` text NOT NULL,
  `cos_es` text NOT NULL,
  `subtitol_agenda_ca` varchar(500) DEFAULT '''''',
  `subtitol_agenda_es` varchar(500) DEFAULT '''''',
  `header` int(11) NOT NULL DEFAULT 1,
  `ordre` varchar(500) NOT NULL DEFAULT '',
  `data` date NOT NULL,
  `destaca_ofertes` tinyint(1) DEFAULT NULL,
  `destaca_agenda` tinyint(1) DEFAULT NULL,
  `destaca_noticies` tinyint(1) DEFAULT NULL,
  `id_sendinblue_ca` int(250) NOT NULL DEFAULT 0,
  `id_sendinblue_es` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `noticia_clients`
--

CREATE TABLE `noticia_clients` (
  `id` int(11) NOT NULL,
  `id_noticia` int(11) NOT NULL,
  `codi_client` varchar(11) DEFAULT NULL,
  `id_element` int(11) NOT NULL,
  `tipus` varchar(15) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `noticia_continguts`
--

CREATE TABLE `noticia_continguts` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_noticia` int(10) NOT NULL,
  `idioma` varchar(2) NOT NULL,
  `param_url` varchar(250) NOT NULL DEFAULT '',
  `titol` varchar(255) NOT NULL DEFAULT '',
  `cos` mediumtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- --------------------------------------------------------

--
-- Estructura de la taula `noticia_establiments`
--

CREATE TABLE `noticia_establiments` (
  `id` int(11) NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `id_noticia` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `noticia_general`
--

CREATE TABLE `noticia_general` (
  `id` int(10) UNSIGNED NOT NULL,
  `actiu` tinyint(1) UNSIGNED DEFAULT NULL,
  `data` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_caducitat` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_creacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `imatge` varchar(150) NOT NULL DEFAULT '',
  `imatge_contingut` tinyint(1) DEFAULT NULL,
  `newsletter` tinyint(1) UNSIGNED NOT NULL DEFAULT 0,
  `pagina_principal` tinyint(1) UNSIGNED NOT NULL DEFAULT 0,
  `sorteig` tinyint(1) NOT NULL DEFAULT 0,
  `sorteig_extern` tinyint(4) NOT NULL DEFAULT 0,
  `patrocinada` tinyint(1) NOT NULL DEFAULT 0,
  `permanent` tinyint(4) NOT NULL DEFAULT 0,
  `ordre` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `codi_client` varchar(15) NOT NULL DEFAULT '',
  `promocions` text DEFAULT NULL,
  `observacions` text DEFAULT NULL,
  `autor` varchar(250) NOT NULL DEFAULT '',
  `logs` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `noticia_noticies`
--

CREATE TABLE `noticia_noticies` (
  `id` int(11) NOT NULL,
  `id_noticia` int(11) NOT NULL DEFAULT 0,
  `id_noticia_relacionada` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `noticia_pobles`
--

CREATE TABLE `noticia_pobles` (
  `id` int(11) NOT NULL,
  `id_noticia` int(11) NOT NULL DEFAULT 0,
  `id_poble` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `noticia_rutes`
--

CREATE TABLE `noticia_rutes` (
  `id` int(11) NOT NULL,
  `id_noticia` int(11) NOT NULL DEFAULT 0,
  `id_ruta` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `oferta_categories`
--

CREATE TABLE `oferta_categories` (
  `id` int(11) NOT NULL,
  `id_oferta` int(11) NOT NULL DEFAULT 0,
  `id_categoria` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `oferta_continguts`
--

CREATE TABLE `oferta_continguts` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_oferta` int(11) NOT NULL DEFAULT 0,
  `idioma` varchar(2) NOT NULL DEFAULT '',
  `param_url` varchar(250) NOT NULL DEFAULT '',
  `titol` varchar(150) NOT NULL DEFAULT '',
  `resum` mediumtext DEFAULT NULL,
  `descripcio` mediumtext DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- --------------------------------------------------------

--
-- Estructura de la taula `oferta_etiquetes`
--

CREATE TABLE `oferta_etiquetes` (
  `id` int(11) NOT NULL,
  `id_oferta` int(11) NOT NULL DEFAULT 0,
  `id_etiqueta` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `oferta_general`
--

CREATE TABLE `oferta_general` (
  `id` int(11) NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `id_poble` int(11) NOT NULL DEFAULT 0,
  `codi_client` varchar(50) NOT NULL DEFAULT '',
  `preu_base` varchar(50) NOT NULL DEFAULT '',
  `preu_oferta` varchar(50) NOT NULL DEFAULT '',
  `preu_desde` tinyint(1) NOT NULL DEFAULT 0,
  `link` varchar(150) NOT NULL DEFAULT '',
  `link_accio` varchar(255) NOT NULL DEFAULT '',
  `data_creacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_inicial` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_final` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `imatge` varchar(250) NOT NULL DEFAULT '',
  `estat` varchar(25) NOT NULL DEFAULT 'borrador',
  `comentaris` text DEFAULT NULL,
  `log` text NOT NULL,
  `newsletter` tinyint(4) DEFAULT NULL,
  `es_oferta` int(11) NOT NULL DEFAULT 0,
  `adjunt` varchar(250) NOT NULL DEFAULT '',
  `latitud` varchar(45) NOT NULL DEFAULT '',
  `longitud` varchar(45) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `pagina_continguts`
--

CREATE TABLE `pagina_continguts` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_pagina` int(10) NOT NULL,
  `idioma` varchar(2) NOT NULL,
  `param_url` varchar(150) NOT NULL DEFAULT '',
  `titol` varchar(255) NOT NULL DEFAULT '',
  `cos` mediumtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- --------------------------------------------------------

--
-- Estructura de la taula `pagina_establiments`
--

CREATE TABLE `pagina_establiments` (
  `id` int(11) NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `id_pagina` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `pagina_general`
--

CREATE TABLE `pagina_general` (
  `id` int(10) UNSIGNED NOT NULL,
  `actiu` tinyint(1) UNSIGNED DEFAULT NULL,
  `newsletter` tinyint(1) UNSIGNED NOT NULL DEFAULT 0,
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_creacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `imatge` varchar(150) NOT NULL DEFAULT '',
  `imatge_header` varchar(150) NOT NULL DEFAULT '',
  `imatge_contingut` tinyint(1) DEFAULT NULL,
  `logs` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `pagina_pobles`
--

CREATE TABLE `pagina_pobles` (
  `id` int(11) NOT NULL,
  `id_pagina` int(11) NOT NULL DEFAULT 0,
  `id_poble` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `pagina_rutes`
--

CREATE TABLE `pagina_rutes` (
  `id` int(11) NOT NULL,
  `id_pagina` int(11) NOT NULL DEFAULT 0,
  `id_ruta` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `poble_certificats`
--

CREATE TABLE `poble_certificats` (
  `id` int(11) UNSIGNED NOT NULL,
  `id_poble` int(11) NOT NULL DEFAULT 0,
  `id_certificat` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `poble_comarques`
--

CREATE TABLE `poble_comarques` (
  `id` int(10) UNSIGNED NOT NULL,
  `param_url` varchar(30) NOT NULL DEFAULT '',
  `id_provincia` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `comarca` varchar(45) NOT NULL DEFAULT '',
  `id_pobles` varchar(500) NOT NULL,
  `param_pobles` varchar(1500) NOT NULL,
  `latitud` varchar(50) NOT NULL,
  `longitud` varchar(50) NOT NULL,
  `nostre` int(11) NOT NULL DEFAULT 0,
  `xs_facebook` varchar(100) NOT NULL DEFAULT '',
  `xs_twitter` varchar(100) NOT NULL DEFAULT '',
  `xs_instagram` varchar(100) NOT NULL DEFAULT '',
  `xs_youtube` varchar(100) NOT NULL DEFAULT '',
  `xs_tiktok` varchar(100) NOT NULL DEFAULT '',
  `web` varchar(250) NOT NULL DEFAULT '',
  `codi_client` varchar(15) NOT NULL DEFAULT '',
  `contracte` varchar(64) NOT NULL DEFAULT '',
  `id_fitxa` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `poble_continguts`
--

CREATE TABLE `poble_continguts` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_poble` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `idioma` varchar(2) NOT NULL DEFAULT '',
  `data_actualitzacio` date NOT NULL DEFAULT '0000-00-00',
  `contingut` text DEFAULT NULL,
  `keywords` text DEFAULT NULL,
  `description` text DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `poble_etiquetes`
--

CREATE TABLE `poble_etiquetes` (
  `id` int(11) NOT NULL,
  `id_poble` int(11) NOT NULL DEFAULT 0,
  `id_etiqueta` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `poble_general`
--

CREATE TABLE `poble_general` (
  `id` int(11) NOT NULL,
  `id_idescat` varchar(10) NOT NULL DEFAULT '',
  `id_comarca` int(11) NOT NULL DEFAULT 0,
  `poble` varchar(50) NOT NULL DEFAULT '',
  `param_url` varchar(150) NOT NULL DEFAULT '',
  `codi_postal` varchar(10) NOT NULL DEFAULT '',
  `extensio` varchar(10) NOT NULL DEFAULT '',
  `altitud` int(11) NOT NULL DEFAULT 0,
  `habitants` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `latitud` varchar(45) NOT NULL DEFAULT '',
  `longitud` varchar(45) NOT NULL DEFAULT '',
  `imatge` varchar(250) NOT NULL DEFAULT '',
  `imatge_header` varchar(250) NOT NULL DEFAULT '',
  `video` varchar(255) NOT NULL DEFAULT '',
  `contracte` int(11) DEFAULT NULL,
  `client` tinyint(1) NOT NULL DEFAULT 0,
  `contracte_banners` int(11) NOT NULL DEFAULT 0,
  `contracte_agenda` int(11) NOT NULL DEFAULT 0,
  `en_campanya` tinyint(1) NOT NULL DEFAULT 0,
  `codi_client` varchar(15) DEFAULT NULL,
  `contractedb` varchar(64) NOT NULL DEFAULT '',
  `password` varchar(20) NOT NULL DEFAULT '',
  `xs_facebook` varchar(100) NOT NULL DEFAULT '',
  `xs_twitter` varchar(100) NOT NULL DEFAULT '',
  `xs_instagram` varchar(100) NOT NULL DEFAULT '',
  `xs_youtube` varchar(100) NOT NULL DEFAULT '',
  `xs_tiktok` varchar(100) NOT NULL DEFAULT '',
  `web` varchar(100) NOT NULL DEFAULT '',
  `telegram` varchar(150) NOT NULL DEFAULT '',
  `whatsapp` varchar(150) NOT NULL DEFAULT '',
  `telefon` varchar(150) NOT NULL DEFAULT '',
  `allow_propostes` tinyint(1) NOT NULL DEFAULT 0,
  `email_continguts` varchar(150) NOT NULL DEFAULT '',
  `email_responsables` varchar(255) NOT NULL DEFAULT '',
  `data_actualitzacio` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE current_timestamp(),
  `comentaris` text DEFAULT NULL,
  `promocions` text DEFAULT NULL,
  `logs` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `poble_provincies`
--

CREATE TABLE `poble_provincies` (
  `id` int(10) UNSIGNED NOT NULL,
  `provincia` varchar(20) NOT NULL DEFAULT ''
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `reserves`
--

CREATE TABLE `reserves` (
  `id` int(11) NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `nom` varchar(50) NOT NULL DEFAULT '',
  `cognoms` varchar(50) NOT NULL DEFAULT '',
  `email` varchar(50) NOT NULL DEFAULT '',
  `telefon` varchar(12) NOT NULL DEFAULT '',
  `pais` varchar(50) NOT NULL DEFAULT '',
  `num_adults` varchar(10) NOT NULL DEFAULT '0',
  `num_nens` varchar(10) NOT NULL DEFAULT '0',
  `comentaris` text DEFAULT NULL,
  `data_entrada` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_sortida` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `mail_ok` varchar(150) NOT NULL DEFAULT '',
  `idioma` varchar(3) NOT NULL DEFAULT ''
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_continguts`
--

CREATE TABLE `ruta_continguts` (
  `id` int(10) UNSIGNED NOT NULL,
  `id_ruta` int(11) NOT NULL DEFAULT 0,
  `idioma` varchar(2) NOT NULL DEFAULT '',
  `param_url` varchar(250) NOT NULL,
  `titol` varchar(150) NOT NULL DEFAULT '',
  `introduccio` text NOT NULL,
  `contingut` text NOT NULL,
  `keywords` text NOT NULL,
  `description` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_establiments`
--

CREATE TABLE `ruta_establiments` (
  `id` int(11) NOT NULL,
  `id_establiment` int(11) NOT NULL DEFAULT 0,
  `id_ruta` int(11) NOT NULL DEFAULT 0,
  `tipus` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_etiquetes`
--

CREATE TABLE `ruta_etiquetes` (
  `id` int(11) NOT NULL,
  `id_ruta` int(11) NOT NULL DEFAULT 0,
  `id_etiqueta` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_general`
--

CREATE TABLE `ruta_general` (
  `id` int(11) NOT NULL,
  `actiu` tinyint(1) NOT NULL DEFAULT 1,
  `data_creacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `data_actualitzacio` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `imatge` varchar(250) NOT NULL DEFAULT '',
  `imatge_header` varchar(250) NOT NULL DEFAULT '',
  `track` varchar(255) NOT NULL DEFAULT '',
  `observacions` text DEFAULT NULL,
  `autor` varchar(250) NOT NULL DEFAULT '',
  `logs` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_mesos`
--

CREATE TABLE `ruta_mesos` (
  `id` int(11) NOT NULL,
  `id_ruta` int(11) NOT NULL DEFAULT 0,
  `mes` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_pobles`
--

CREATE TABLE `ruta_pobles` (
  `id` int(11) NOT NULL,
  `id_ruta` int(11) NOT NULL DEFAULT 0,
  `id_poble` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_public`
--

CREATE TABLE `ruta_public` (
  `id` int(11) NOT NULL,
  `id_ruta` int(11) NOT NULL DEFAULT 0,
  `id_public` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_tags`
--

CREATE TABLE `ruta_tags` (
  `id` int(11) NOT NULL,
  `id_ruta` int(11) NOT NULL DEFAULT 0,
  `tag` varchar(75) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `ruta_tematica`
--

CREATE TABLE `ruta_tematica` (
  `id` int(11) NOT NULL,
  `id_ruta` int(11) NOT NULL DEFAULT 0,
  `id_tematica` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `slides`
--

CREATE TABLE `slides` (
  `id` int(11) NOT NULL,
  `data_inicial` date NOT NULL,
  `data_final` date NOT NULL,
  `ordre` int(11) NOT NULL DEFAULT 0,
  `imatge` varchar(255) NOT NULL DEFAULT '',
  `actiu` int(1) NOT NULL DEFAULT 1,
  `text_ca` varchar(250) NOT NULL,
  `text_es` varchar(250) NOT NULL,
  `text_en` varchar(250) NOT NULL,
  `text_fr` varchar(250) NOT NULL,
  `link_ca` varchar(250) NOT NULL,
  `link_es` varchar(250) NOT NULL,
  `link_en` varchar(250) NOT NULL,
  `link_fr` varchar(250) NOT NULL,
  `target` varchar(250) NOT NULL,
  `icona` varchar(150) NOT NULL,
  `observacions` text NOT NULL,
  `logs` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `sorteig`
--

CREATE TABLE `sorteig` (
  `id` int(11) NOT NULL,
  `id_sorteig` int(11) NOT NULL DEFAULT 0,
  `nom` varchar(50) NOT NULL DEFAULT '',
  `cognoms` varchar(50) NOT NULL DEFAULT '',
  `email` varchar(50) NOT NULL DEFAULT '',
  `telefon` varchar(12) NOT NULL DEFAULT '',
  `pais` varchar(50) NOT NULL DEFAULT '',
  `idioma` varchar(2) NOT NULL DEFAULT '',
  `data_alta` datetime NOT NULL DEFAULT '0000-00-00 00:00:00'
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `subscripcions`
--

CREATE TABLE `subscripcions` (
  `id` int(11) NOT NULL,
  `nom` varchar(50) NOT NULL DEFAULT '',
  `cognoms` varchar(50) NOT NULL DEFAULT '',
  `email` varchar(50) NOT NULL DEFAULT '',
  `telefon` varchar(12) NOT NULL DEFAULT '',
  `pais` varchar(50) NOT NULL DEFAULT '',
  `idioma` varchar(2) NOT NULL DEFAULT '',
  `data_alta` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `hash` varchar(32) NOT NULL DEFAULT '',
  `data_baixa` datetime DEFAULT NULL,
  `origen` varchar(20) NOT NULL DEFAULT 'C'
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `suggeriments`
--

CREATE TABLE `suggeriments` (
  `id` int(10) UNSIGNED NOT NULL,
  `idioma` varchar(2) NOT NULL DEFAULT '',
  `nom` varchar(45) NOT NULL DEFAULT '',
  `cognoms` varchar(150) NOT NULL,
  `data` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `email` varchar(45) NOT NULL DEFAULT '',
  `telefon` varchar(15) NOT NULL,
  `assumpte` varchar(150) NOT NULL DEFAULT '',
  `missatge` text NOT NULL,
  `estat` char(1) NOT NULL DEFAULT ''
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `rol` varchar(15) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(128) NOT NULL,
  `telefon` varchar(25) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `visites_dia`
--

CREATE TABLE `visites_dia` (
  `data` date NOT NULL,
  `pagines` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `visites` int(10) UNSIGNED NOT NULL DEFAULT 0,
  `amb_cookie` int(10) UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `visites_dia_hashes`
--

CREATE TABLE `visites_dia_hashes` (
  `data` date NOT NULL,
  `hash` char(32) NOT NULL,
  `amb_cookie` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `visites_hora`
--

CREATE TABLE `visites_hora` (
  `data` date NOT NULL,
  `hora` tinyint(4) NOT NULL,
  `pagines` int(10) UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de la taula `xs_posts`
--

CREATE TABLE `xs_posts` (
  `id` int(11) NOT NULL,
  `tipus_element` varchar(25) NOT NULL,
  `id_element` int(11) NOT NULL,
  `xarxa` varchar(100) NOT NULL,
  `data` datetime NOT NULL,
  `data_generat` datetime NOT NULL,
  `text` text NOT NULL,
  `imatge` varchar(255) NOT NULL,
  `link` varchar(255) NOT NULL,
  `csv` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Ãndexs per a les taules bolcades
--

--
-- Ãndexs per a la taula `agenda_categories`
--
ALTER TABLE `agenda_categories`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `agenda_clients`
--
ALTER TABLE `agenda_clients`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_agenda` (`id_agenda`);

--
-- Ãndexs per a la taula `agenda_continguts`
--
ALTER TABLE `agenda_continguts`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `agenda_dates`
--
ALTER TABLE `agenda_dates`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_dates` (`id_agenda`,`data_inici`,`data_final`);

--
-- Ãndexs per a la taula `agenda_etiquetes`
--
ALTER TABLE `agenda_etiquetes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `agenda_general`
--
ALTER TABLE `agenda_general`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_estat` (`activa`,`arxivada`,`baixa`);

--
-- Ãndexs per a la taula `agenda_oberta`
--
ALTER TABLE `agenda_oberta`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `agenda_pobles`
--
ALTER TABLE `agenda_pobles`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `agendes_externes`
--
ALTER TABLE `agendes_externes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `analytics_data`
--
ALTER TABLE `analytics_data`
  ADD UNIQUE KEY `idx_name` (`tipus_element`,`id`,`mes`,`any`,`tipus`,`accio`,`categoria`);

--
-- Ãndexs per a la taula `banners_ubicacio`
--
ALTER TABLE `banners_ubicacio`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `banner_clients`
--
ALTER TABLE `banner_clients`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `banner_contingut`
--
ALTER TABLE `banner_contingut`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `banner_general`
--
ALTER TABLE `banner_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `ci_captcha`
--
ALTER TABLE `ci_captcha`
  ADD PRIMARY KEY (`captcha_id`),
  ADD KEY `word` (`word`);

--
-- Ãndexs per a la taula `ci_sessions`
--
ALTER TABLE `ci_sessions`
  ADD PRIMARY KEY (`session_id`),
  ADD KEY `last_activity_idx` (`last_activity`);

--
-- Ãndexs per a la taula `client`
--
ALTER TABLE `client`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `comunicacions`
--
ALTER TABLE `comunicacions`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `config`
--
ALTER TABLE `config`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id` (`id`);

--
-- Ãndexs per a la taula `counters`
--
ALTER TABLE `counters`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `destacats`
--
ALTER TABLE `destacats`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `establiment_certificats`
--
ALTER TABLE `establiment_certificats`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `establiment_continguts`
--
ALTER TABLE `establiment_continguts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_establiment_contingut_1` (`id_establiment`);

--
-- Ãndexs per a la taula `establiment_etiquetes`
--
ALTER TABLE `establiment_etiquetes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `establiment_general`
--
ALTER TABLE `establiment_general`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `param_url` (`param_url`);

--
-- Ãndexs per a la taula `establiment_pobles`
--
ALTER TABLE `establiment_pobles`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_establiment_pobles` (`id_establiment`),
  ADD KEY `FK_establiment_pobles2` (`id_poble`);

--
-- Ãndexs per a la taula `establiment_tipus`
--
ALTER TABLE `establiment_tipus`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `fitxa`
--
ALTER TABLE `fitxa`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `hash` (`hash`);

--
-- Ãndexs per a la taula `generic_categoria_agenda`
--
ALTER TABLE `generic_categoria_agenda`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `generic_categoria_oferta`
--
ALTER TABLE `generic_categoria_oferta`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `generic_certificats`
--
ALTER TABLE `generic_certificats`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `generic_public`
--
ALTER TABLE `generic_public`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `generic_tematiques`
--
ALTER TABLE `generic_tematiques`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `generic_tipus_establiment`
--
ALTER TABLE `generic_tipus_establiment`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `generic_ubicacions`
--
ALTER TABLE `generic_ubicacions`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `idiomes`
--
ALTER TABLE `idiomes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `landing_categories`
--
ALTER TABLE `landing_categories`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `landing_categories_continguts`
--
ALTER TABLE `landing_categories_continguts`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `landing_categories_general`
--
ALTER TABLE `landing_categories_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `landing_continguts`
--
ALTER TABLE `landing_continguts`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `landing_etiquetes`
--
ALTER TABLE `landing_etiquetes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `landing_etiquetes_general`
--
ALTER TABLE `landing_etiquetes_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `landing_general`
--
ALTER TABLE `landing_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `newsletter_continguts`
--
ALTER TABLE `newsletter_continguts`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `newsletter_general`
--
ALTER TABLE `newsletter_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `noticia_clients`
--
ALTER TABLE `noticia_clients`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `noticia_continguts`
--
ALTER TABLE `noticia_continguts`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `noticia_establiments`
--
ALTER TABLE `noticia_establiments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_noticia_establiments_F1` (`id_noticia`),
  ADD KEY `FK_noticia_establiments_F2` (`id_establiment`);

--
-- Ãndexs per a la taula `noticia_general`
--
ALTER TABLE `noticia_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `noticia_noticies`
--
ALTER TABLE `noticia_noticies`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `noticia_pobles`
--
ALTER TABLE `noticia_pobles`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_noticia_pobles_F2` (`id_poble`),
  ADD KEY `FK_noticia_pobles_F1` (`id_noticia`);

--
-- Ãndexs per a la taula `noticia_rutes`
--
ALTER TABLE `noticia_rutes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `oferta_categories`
--
ALTER TABLE `oferta_categories`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `oferta_continguts`
--
ALTER TABLE `oferta_continguts`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `oferta_etiquetes`
--
ALTER TABLE `oferta_etiquetes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `oferta_general`
--
ALTER TABLE `oferta_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `pagina_continguts`
--
ALTER TABLE `pagina_continguts`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `pagina_establiments`
--
ALTER TABLE `pagina_establiments`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `pagina_general`
--
ALTER TABLE `pagina_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `pagina_pobles`
--
ALTER TABLE `pagina_pobles`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `pagina_rutes`
--
ALTER TABLE `pagina_rutes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `poble_certificats`
--
ALTER TABLE `poble_certificats`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `poble_comarques`
--
ALTER TABLE `poble_comarques`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_poble_comarques_1` (`id_provincia`);

--
-- Ãndexs per a la taula `poble_continguts`
--
ALTER TABLE `poble_continguts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_poble_continguts_1` (`id_poble`);

--
-- Ãndexs per a la taula `poble_etiquetes`
--
ALTER TABLE `poble_etiquetes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `poble_general`
--
ALTER TABLE `poble_general`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_poble_general_1` (`id_comarca`),
  ADD KEY `idx_latitud` (`latitud`),
  ADD KEY `idx_longitud` (`longitud`),
  ADD KEY `idx_lat_lng` (`latitud`,`longitud`);

--
-- Ãndexs per a la taula `poble_provincies`
--
ALTER TABLE `poble_provincies`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `reserves`
--
ALTER TABLE `reserves`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `ruta_continguts`
--
ALTER TABLE `ruta_continguts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_ruta_continguts_F1` (`id_ruta`);

--
-- Ãndexs per a la taula `ruta_establiments`
--
ALTER TABLE `ruta_establiments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_ruta_establiments_F1` (`id_ruta`),
  ADD KEY `FK_ruta_establiments_F2` (`id_establiment`);

--
-- Ãndexs per a la taula `ruta_etiquetes`
--
ALTER TABLE `ruta_etiquetes`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `ruta_general`
--
ALTER TABLE `ruta_general`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `ruta_mesos`
--
ALTER TABLE `ruta_mesos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_ruta_mesos_F1` (`id_ruta`);

--
-- Ãndexs per a la taula `ruta_pobles`
--
ALTER TABLE `ruta_pobles`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_ruta_pobles2` (`id_poble`),
  ADD KEY `FK_ruta_pobles_F1` (`id_ruta`);

--
-- Ãndexs per a la taula `ruta_public`
--
ALTER TABLE `ruta_public`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_ruta_public_F1` (`id_ruta`);

--
-- Ãndexs per a la taula `ruta_tags`
--
ALTER TABLE `ruta_tags`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_ruta_tags_F1` (`id_ruta`);

--
-- Ãndexs per a la taula `ruta_tematica`
--
ALTER TABLE `ruta_tematica`
  ADD PRIMARY KEY (`id`),
  ADD KEY `FK_ruta_tematica_F1` (`id_ruta`);

--
-- Ãndexs per a la taula `slides`
--
ALTER TABLE `slides`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `sorteig`
--
ALTER TABLE `sorteig`
  ADD PRIMARY KEY (`id_sorteig`,`email`),
  ADD KEY `id` (`id`);

--
-- Ãndexs per a la taula `subscripcions`
--
ALTER TABLE `subscripcions`
  ADD PRIMARY KEY (`email`),
  ADD KEY `id` (`id`);

--
-- Ãndexs per a la taula `suggeriments`
--
ALTER TABLE `suggeriments`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- Ãndexs per a la taula `visites_dia`
--
ALTER TABLE `visites_dia`
  ADD PRIMARY KEY (`data`);

--
-- Ãndexs per a la taula `visites_dia_hashes`
--
ALTER TABLE `visites_dia_hashes`
  ADD PRIMARY KEY (`data`,`hash`);

--
-- Ãndexs per a la taula `visites_hora`
--
ALTER TABLE `visites_hora`
  ADD PRIMARY KEY (`data`,`hora`);

--
-- Ãndexs per a la taula `xs_posts`
--
ALTER TABLE `xs_posts`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT per les taules bolcades
--

--
-- AUTO_INCREMENT per la taula `agenda_categories`
--
ALTER TABLE `agenda_categories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `agenda_clients`
--
ALTER TABLE `agenda_clients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `agenda_continguts`
--
ALTER TABLE `agenda_continguts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `agenda_dates`
--
ALTER TABLE `agenda_dates`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `agenda_etiquetes`
--
ALTER TABLE `agenda_etiquetes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `agenda_general`
--
ALTER TABLE `agenda_general`
  MODIFY `id` int(255) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `agenda_pobles`
--
ALTER TABLE `agenda_pobles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `agendes_externes`
--
ALTER TABLE `agendes_externes`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `banners_ubicacio`
--
ALTER TABLE `banners_ubicacio`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `banner_clients`
--
ALTER TABLE `banner_clients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `banner_contingut`
--
ALTER TABLE `banner_contingut`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `banner_general`
--
ALTER TABLE `banner_general`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ci_captcha`
--
ALTER TABLE `ci_captcha`
  MODIFY `captcha_id` bigint(13) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `client`
--
ALTER TABLE `client`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `comunicacions`
--
ALTER TABLE `comunicacions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `config`
--
ALTER TABLE `config`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `counters`
--
ALTER TABLE `counters`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `destacats`
--
ALTER TABLE `destacats`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `establiment_certificats`
--
ALTER TABLE `establiment_certificats`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `establiment_continguts`
--
ALTER TABLE `establiment_continguts`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `establiment_etiquetes`
--
ALTER TABLE `establiment_etiquetes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `establiment_general`
--
ALTER TABLE `establiment_general`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `establiment_pobles`
--
ALTER TABLE `establiment_pobles`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `establiment_tipus`
--
ALTER TABLE `establiment_tipus`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `fitxa`
--
ALTER TABLE `fitxa`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `generic_categoria_agenda`
--
ALTER TABLE `generic_categoria_agenda`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `generic_certificats`
--
ALTER TABLE `generic_certificats`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `generic_public`
--
ALTER TABLE `generic_public`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `generic_tematiques`
--
ALTER TABLE `generic_tematiques`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `generic_ubicacions`
--
ALTER TABLE `generic_ubicacions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `landing_categories`
--
ALTER TABLE `landing_categories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `landing_categories_continguts`
--
ALTER TABLE `landing_categories_continguts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `landing_categories_general`
--
ALTER TABLE `landing_categories_general`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `landing_continguts`
--
ALTER TABLE `landing_continguts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `landing_etiquetes`
--
ALTER TABLE `landing_etiquetes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `landing_etiquetes_general`
--
ALTER TABLE `landing_etiquetes_general`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `landing_general`
--
ALTER TABLE `landing_general`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `newsletter_continguts`
--
ALTER TABLE `newsletter_continguts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `newsletter_general`
--
ALTER TABLE `newsletter_general`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `noticia_clients`
--
ALTER TABLE `noticia_clients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `noticia_continguts`
--
ALTER TABLE `noticia_continguts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `noticia_establiments`
--
ALTER TABLE `noticia_establiments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `noticia_general`
--
ALTER TABLE `noticia_general`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `noticia_noticies`
--
ALTER TABLE `noticia_noticies`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `noticia_pobles`
--
ALTER TABLE `noticia_pobles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `noticia_rutes`
--
ALTER TABLE `noticia_rutes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `oferta_categories`
--
ALTER TABLE `oferta_categories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `oferta_continguts`
--
ALTER TABLE `oferta_continguts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `oferta_etiquetes`
--
ALTER TABLE `oferta_etiquetes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `oferta_general`
--
ALTER TABLE `oferta_general`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `pagina_continguts`
--
ALTER TABLE `pagina_continguts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `pagina_establiments`
--
ALTER TABLE `pagina_establiments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `pagina_general`
--
ALTER TABLE `pagina_general`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `pagina_pobles`
--
ALTER TABLE `pagina_pobles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `pagina_rutes`
--
ALTER TABLE `pagina_rutes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `poble_certificats`
--
ALTER TABLE `poble_certificats`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `poble_comarques`
--
ALTER TABLE `poble_comarques`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `poble_continguts`
--
ALTER TABLE `poble_continguts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `poble_etiquetes`
--
ALTER TABLE `poble_etiquetes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `poble_general`
--
ALTER TABLE `poble_general`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `poble_provincies`
--
ALTER TABLE `poble_provincies`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `reserves`
--
ALTER TABLE `reserves`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_continguts`
--
ALTER TABLE `ruta_continguts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_establiments`
--
ALTER TABLE `ruta_establiments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_etiquetes`
--
ALTER TABLE `ruta_etiquetes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_general`
--
ALTER TABLE `ruta_general`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_mesos`
--
ALTER TABLE `ruta_mesos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_pobles`
--
ALTER TABLE `ruta_pobles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_public`
--
ALTER TABLE `ruta_public`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_tags`
--
ALTER TABLE `ruta_tags`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `ruta_tematica`
--
ALTER TABLE `ruta_tematica`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `slides`
--
ALTER TABLE `slides`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `sorteig`
--
ALTER TABLE `sorteig`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `subscripcions`
--
ALTER TABLE `subscripcions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `suggeriments`
--
ALTER TABLE `suggeriments`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT per la taula `xs_posts`
--
ALTER TABLE `xs_posts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

